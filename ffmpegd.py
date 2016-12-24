#!/usr/bin/env python
# Written by Sean Wareham August 25, 2016


"""
Program to batch convert a directory of audio or video files with ffmpeg and almost any combination of ffmpeg parameters.
ffmpegd will recursively search an input directory and recreate the same directory structure in the output directory
specified. If no output directory is specified, the output directory will be set to  "{input_directory}-converted"
If no input directory is specified, the current working directory will be used.

Required arguments specific to ffmpegd (opposed to ffmpeg) only include "--extension" which is used to define
the file extension to be used for output files (output files will retain their name, but will replace the extension
with the input extension as appropriate). This extension will also be used for the default behavior in determining which
files in the input directory should be converted. E.g. --extension mp4 will result in files with video extensions being
found and converted. --extension mp3 would result in audio files being found and converted.

ffmpegd supports all ffmpeg arguments with two exceptions:
 1.) "-i" whose behavior has been overridden by the --inputdirectory argument
 2.) Commands that require parameters to occur positionally before the "-i" flag used by ffmpeg. These commands
 generally relate to selecting specific time segments within a file. As these are likely to be relevant on a file-by-file
 basis, it is unlikely this feature would ever be used in batches. If the demand were to arise, I can put a workaround
 in place

 ffmpegd additionally supports regex matching instead of extension matching. Regex can be specified with the --regex
 option and must follow python regex syntax (python escaping should not be included although the pattern should be
 inside quotes. NOTE: collision with shell expansion has not been tested and errors may arise.

Examples:
    $ ffmpegd --inputdirectory /path/to/videos/ --extension mp4 -acodec libfdk_aac -vcodec libx264
    All files with file extensions of traditional video files will be located and converted to mp4 videos using the
    libfdk_aac audio codec and the libx264 video codec. The input directory structure will be replicated
    at /path/to/videos-converted/ (only directories that contain valid input files will be recreated with output files
    $ ffmpegd -i /path/to/videos/ -e mp4 -acodec libfdk_aac -vcodec libx264
    Same as above
    $ ffmpegd -e mp4 -acodec libfdk_aac -vcodec libx264
    Same as above, except the input directory is defined as the current working directory (i.e., $PWD)
    $ ffmpegd -e mp4 -acodec libfdk_aac -vcodec libx264 --outputdirectory /output/video/path
    Same as above, except the output directory structure will begin at /output/video/path
    $ ffmpegd -e mp4 -acodec libfdk_aac -vcodec libx264 --outputdirectory /output/video/path --dry-run
    The previous example will be simulated but no conversions will take place and no directory structures will be created

"""

import argparse
import os
import subprocess
import re

FFMPEG_BASE = ['ffmpeg']
VIDEO_EXTENSIONS = ["mp4", "avi", "mov", "mkv", "flv", "wmv", "m4v", "webm"]
# Note: ogg *may* be audio-video but usually shouldn't be
AUDIO_EXTENSIONS = ["mp3", "m4a", "opus", "ape", "wav", "aac", "ogg", "oga", "aiff", "flac", "alac"]


def _execute_command(command):
    """
    Spawn a subprocess to execute a command and retrieve its output (as bytes in Python 3, as str in Python 2)
    :param command: Iterable of commands to be executed (handles whitespace escaping automatically)
    :return: Output from executed subprocess (as bytes in Python 3, as str in Python 2)
    """
    try:
        return subprocess.check_output(command)
    except subprocess.CalledProcessError:
        return None


def _get_output(command):
    """
    Spawn a subprocess to execute a command and retrieve its output as utf-8 str (unicode in Python 2)
    :param command: Iterable of commands to be executed (handles whitespace escaping automatically)
    :return: Output from executed subprocess as utf-8 str (unicode in Python 2)
    """
    output = _execute_command(command)
    if output is None:
        return None
    else:
        return output.decode('utf-8').strip()


def _get_args():
    """
    Construct args from sys.argv using argparser. Performs most, but not all, argument validation
    :return: Tuple of known_args, unknown_args where known args is an argparser namespace and unknown_args is a list of
    arguments in the form ["--flag", "flag value"]
    """
    parser = argparse.ArgumentParser(description="Batch convert a directory with ffmpeg and any args")
    parser.add_argument("--extension", "-e", help='The file extension for output files', required=True,
                        choices=VIDEO_EXTENSIONS + AUDIO_EXTENSIONS)
    parser.add_argument("--inputdirectory", "-i",
                        help="Input directory to convert. Note, this does not perform shell expansion" +
                             " (i.e., '.'  will not expand to the current working directory)",
                        required=False)

    parser.add_argument("--outputdirectory", "-o",
                        help="Input output directory Note, this does not perform shell expansion" +
                             " (i.e., '.'  will not expand to the current working directory)", required=False)
    parser.add_argument("--dry-run", "-d", help="Emulate the slated action with no changes to the system",
                        action='store_true', required=False)
    parser.add_argument("--regex", help="Regex pattern to match input files", required=False)
    known_args, unknown_args = parser.parse_known_args()
    if known_args.inputdirectory is None:
        known_args.inputdirectory = os.getcwd()
    # Remove trailing slash if present. Fixes bug where "[converted]" was the start of a subdirectory instead of
    # concatenated onto the inputdirectory path.
    # Note: if bugs arise with the output directory, this is a good place to check
    known_args.inputdirectory = os.path.normpath(known_args.inputdirectory)
    if known_args.outputdirectory is None:
        output_directory_parent = os.path.dirname(known_args.inputdirectory)
        output_directory_name = os.path.basename(known_args.inputdirectory) + "[converted]"
        known_args.outputdirectory = os.path.join(output_directory_parent, output_directory_name)
    _validate_known_args(known_args)
    return known_args, unknown_args


def _validate_known_args(known_args):
    """
    Validate args that cannot cleanly be validated by argparser. If arguments are not valid, raise an error.
    :param known_args:
    :return:
    """
    if not os.path.isdir(known_args.inputdirectory):
        raise IsADirectoryError(known_args.inputdirectory + "is not a valid directory!")


def _regex_is_desired_file(full_path, regex_pattern):
    """
    Returns True if the basename of a file matches the regex pattern
    :param full_path: The path of the input file
    :param regex_pattern: The regular expression pattern to match, as a string
    :return: True if the basename of a file matches the regex pattern, else False
    """
    pattern = re.compile(regex_pattern)
    basename = os.path.basename(full_path)
    return pattern.match(basename) is not None


def _extension_is_desired_file(full_path, extension):
    """
    Returns True if the file ends with the given file extension of a file matches the regex pattern
    :param full_path: The path of the input file
    :param extension: The extension to match without a "." e.g., "mkv" or "mp4"
    :return: True if the extension of a file matches the input extension
    """
    test_extension = os.path.splitext(full_path)[-1][1:]
    if extension in AUDIO_EXTENSIONS:
        return test_extension in AUDIO_EXTENSIONS
    elif extension in VIDEO_EXTENSIONS:
        return test_extension in VIDEO_EXTENSIONS
    else:
        return False


# TODO: refactor to use an actual structure
# TODO: remove mkdir -p from dry run; not strictly accurate, and not emulated well as implementaiton relies on checking
# if the directory itself exists. should assume any top level directories (set to be created)
#  that appear in bottom level directories don't exist
def run(known_args, unknown_args):
    dry_run = known_args.dry_run
    input_directory = known_args.inputdirectory
    extension = known_args.extension
    output_directory = known_args.outputdirectory
    regex_pattern = known_args.regex
    desired_input_paths = []
    for path, dirs, files in os.walk(input_directory):
        for f in files:
            full_path = os.path.join(path, f)
            if regex_pattern is not None:
                is_desired = _regex_is_desired_file(full_path, regex_pattern)
            else:
                is_desired = _extension_is_desired_file(full_path, extension)
            if is_desired:
                desired_input_paths.append(full_path)
    # reverse order so that deeper paths are called first (fewer calls to makedirs)
    desired_input_paths = desired_input_paths[::-1]
    for input_path in desired_input_paths:
        output_path = input_path.replace(input_directory, output_directory, 1)
        output_pardir = os.path.dirname(output_path)
        # Set output_path to have correct file extension
        output_path = os.path.join(output_pardir,
                                   os.path.splitext(os.path.basename(output_path))[0] + "." + extension)
        if not os.path.exists(output_pardir):
            if dry_run:
                print("mkdir -p " + output_pardir)
            else:
                os.makedirs(output_pardir)
        command = FFMPEG_BASE + ['-i', input_path] + unknown_args + [output_path]
        if dry_run:
            whitespace_escaped_command = ["\"" + c + "\"" if " " in c else c for c in command]
            print(" ".join(whitespace_escaped_command))
        else:
            _execute_command(command)


def main():
    known_args, unknown_args = _get_args()
    run(known_args, unknown_args)


if __name__ == "__main__":
    main()
