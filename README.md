# Python 3 Mouse Daemon

This is a small python daemon (non-forking, so use it with systemd or something like that) primarily aimed for headless servers to use a mouse as source of input.
I wrote it to control a PulseAudio instance's volume level on my Bluetooth A2DP sink.

I did not find any good Python module to get raw mouse events from /dev/input/mice or /dev/input/mouseX that supported mouse wheel since this needs protocol switching to 4-byte-status-responses, so I wrote this (which does not imply that this is a good module!).

The code supports Default mouse protocol (3 buttons), IntelliMouse protocol (3 buttons + scroll wheel) and Exploerer Mouse protocol (5 buttons + scroll wheel(s)).

MouseDaemon is the daemon-like class that makes it possible to listen for mouse events. However, you'll need another class that supplies some kind of event handling, look at PulseAudioController for a simple example.

This is in fact a really simple script, but it serves its purpose.

A short overview of the files and classes:

* **Mouse.py**: Contains the class **Mouse** that takes a mouse character device file descriptor and handles all the mouse-talking stuff. Also contains **MouseData**, the data structure used to transport mouse states.
* **MouseDaemon.py**: Contains an abstract **MouseEventResponder** class as a prototype what an actual responder should implement. Contains the **MouseDaemon** class, which handles opening of device file, creates a *Mouse instance*, switches to the highest protocol available and finally provides a event handling loop that receives mouse events and sends them to a supplied *MouseEventResponder instance*.
* **PulseAudioController.py**: Contains a simple sample implementation to control a PulseAudio server.
* **UnixHelper.py**: Contains a function to drop privileges.

This does not include any form of multithreading, especially mouse querying is a blocking call. If you don't touch the mouse, the whole process will block. So you see, this is not intended to be used as a mouse server but rather a small controller daemon to trigger *simple* tasks based on mouse input. Or you might want to see it as an example on how to connect with a mouse device file in Python. 
