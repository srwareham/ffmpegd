ffmpegd 
=======

*\*Placeholder Documentation\**
===========================

ffmpegd is a program to batch convert a directory of audio or video files with ffmpeg and almost any combination of ffmpeg parameters.
ffmpegd will recursively search an input directory and recreate the same directory structure in the output directory
specified. If no output directory is specified, the output directory will be set to  "{input_directory}-converted"
If no input directory is specified, the current working directory will be used.

Required arguments specific to ffmpegd (opposed to ffmpeg) only include "--extension" which is used to define
the file extension to be used for output files (output files will retain their name, but will replace the extension
with the input extension as appropriate). This extension will also be used for the default behavior in determining which
files in the input directory should be converted. E.g. --extension mp4 will result in files with video extensions being
found and converted. --extension mp3 would result in audio files being found and converted.

ffmpegd supports all ffmpeg arguments with two exceptions:
 1. "-i" whose behavior has been overridden by the --input-directory argument
 
 2. Commands that require parameters to occur positionally before the "-i" flag used by ffmpeg. These commands generally relate to selecting specific time segments within a file. As these are likely to be relevant on a file-by-file basis, it is unlikely this feature would ever be used in batches. If the demand were to arise, I can put a workaround in place

 ffmpegd additionally supports regex matching instead of extension matching. Regex can be specified with the --regex
 option and must follow python regex syntax (python escaping should not be included although the pattern should be
 inside quotes. NOTE: collision with shell expansion has not been tested and errors may arise.


Examples
--------


.. code-block:: bash

    $ ffmpegd --input-directory /path/to/videos/ --extension mp4 -acodec libfdk_aac -vcodec libx264
    All files with file extensions of traditional video files will be located and converted to mp4 videos using the libfdk_aac audio codec and the libx264 video codec. The input directory structure will be replicated at /path/to/videos-converted/ (only directories that contain valid input files will be recreated with output files
    $ ffmpegd -i /path/to/videos/ -e mp4 -acodec libfdk_aac -vcodec libx264
    Same as above
    $ ffmpegd -e mp4 -acodec libfdk_aac -vcodec libx264
    Same as above, except the input directory is defined as the current working directory (i.e., $PWD)
    $ ffmpegd -e mp4 -acodec libfdk_aac -vcodec libx264 --output-directory /output/video/path
    Same as above, except the output directory structure will begin at /output/video/path
    $ ffmpegd -e mp4 -acodec libfdk_aac -vcodec libx264 --output-directory /output/video/path --dry-run
    The previous example will be simulated but no conversions will take place and no directory structures will be created


