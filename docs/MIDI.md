# Some notes on MIDI integration

When enabled, the bot sends simple MIDI note messages on song change. This can be used to trigger other software or hardware that listens for MIDI input.
I use Nestdrop and have set it up to listen for these using a MIDI note trigger, I've set velocity to be random between 1-100, and in Nestdrop I change preset based on these with a normal Transition if <= 90 and a hard cut if > 90, this way I get a bit of variety in transitions.
