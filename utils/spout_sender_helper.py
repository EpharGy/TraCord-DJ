# pyright: reportAttributeAccessIssue=false
SPOUT_SIZE = 1080
import threading
import time
import traceback
import SpoutGL
from PIL import Image
from config.settings import Settings

try:
    # type: ignore[import]
    from SpoutGL import SpoutSender
    import glfw
    import OpenGL.GL as gl
    SPOUTGL_AVAILABLE = True
except ImportError:
    SpoutSender = None
    glfw = None
    gl = None
    SPOUTGL_AVAILABLE = False

class SpoutGLHelper:
    """
    Helper class to manage a hidden OpenGL context and send PIL images via SpoutGL.
    Usage:
        helper = SpoutGLHelper(sender_name="TraCordDJ CoverArt")
        helper.start()
        helper.send_pil_image(pil_img)
        helper.stop()
    """
    def __init__(self, sender_name="TraCordDJ CoverArt", width=SPOUT_SIZE, height=SPOUT_SIZE):
        self.sender_name = sender_name
        self.width = width
        self.height = height
        self._thread = None
        self._running = False
        self._pending_img = None
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._sender = None
        self._window = None
        self._fade_queue = []

    def start(self):
        if not SPOUTGL_AVAILABLE:
            raise RuntimeError("SpoutGL is not installed.")
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._window:
            glfw.destroy_window(self._window) # type: ignore # type: ignore
            glfw.terminate() # type: ignore
        self._sender = None
        self._window = None

    def send_pil_image(self, pil_img):
        if not self._running:
            return
        with self._lock:
            if not hasattr(self, '_last_img'):
                self._last_img = None
            frames = getattr(Settings, 'FADE_FRAMES', 30)
            duration = getattr(Settings, 'FADE_DURATION', 1.0)
            if self._last_img is not None and Settings.FADE_STYLE in ("fade", "crossfade"):
                self._fade_to_image(self._last_img, pil_img, frames=frames, duration=duration, style=Settings.FADE_STYLE)
            else:
                self._pending_img = pil_img.copy()
            self._last_img = pil_img.copy()

    def _fade_to_image(self, img_from, img_to, frames=30, duration=1.0, style="fade"):
        # frames: total frames for the transition
        # duration: total duration in seconds
        if style == "fade":
            steps = max(1, frames // 2)
            delay = duration / frames
        else:  # crossfade or other
            steps = frames
            delay = duration / frames
        frames_list = []
        img_from = img_from.convert("RGBA").resize((SPOUT_SIZE, SPOUT_SIZE))
        img_to = img_to.convert("RGBA").resize((SPOUT_SIZE, SPOUT_SIZE))
        if style == "fade":
            transparent = Image.new("RGBA", (SPOUT_SIZE, SPOUT_SIZE), (0, 0, 0, 0))
            for i in range(steps):
                alpha = 1 - (i / steps)
                blended = Image.blend(img_from, transparent, 1 - alpha)
                frames_list.append(blended.copy())
            for i in range(steps):
                alpha = (i + 1) / steps
                blended = Image.blend(transparent, img_to, alpha)
                frames_list.append(blended.copy())
        elif style == "crossfade":
            for i in range(steps + 1):
                alpha = i / steps
                blended = Image.blend(img_from, img_to, alpha)
                frames_list.append(blended.copy())
        else:
            frames_list.append(img_to.copy())
        self._fade_queue = frames_list
        self._fade_delay = delay

    def _run(self):
        try:
            if not glfw.init(): # type: ignore # type: ignore
                print("[SpoutGL] Failed to init GLFW")
                return
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE) # type: ignore
            self._window = glfw.create_window(self.width, self.height, "SpoutGL Hidden", None, None) # type: ignore
            if not self._window:
                print("[SpoutGL] Failed to create GLFW window")
                glfw.terminate() # type: ignore
                return
            glfw.make_context_current(self._window) # type: ignore
            self._sender = SpoutSender() # type: ignore
            self._sender.setSenderName(self.sender_name)
            self._ready.set()
            while self._running:
                img = None
                delay = 0.02
                with self._lock:
                    if self._fade_queue:
                        img = self._fade_queue.pop(0)
                        delay = getattr(self, '_fade_delay', 0.08)
                    elif self._pending_img is not None:
                        img = self._pending_img
                        self._pending_img = None
                if img is not None:
                    self._send_image(img)
                    time.sleep(delay)
                else:
                    time.sleep(0.02)
        except Exception as e:
            print(f"[SpoutGL] Error in sender thread: {e}\n{traceback.format_exc()}")
        finally:
            self._sender = None
            if self._window:
                glfw.destroy_window(self._window) # type: ignore
                glfw.terminate() # type: ignore

    def _send_image(self, pil_img):
        img = pil_img.convert("RGBA").resize((SPOUT_SIZE, SPOUT_SIZE))
        img_bytes = img.tobytes()
        # Upload to OpenGL texture
        tex_id = gl.glGenTextures(1) # type: ignore
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id) # type: ignore
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, SPOUT_SIZE, SPOUT_SIZE, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_bytes) # type: ignore
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR) # type: ignore
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR) # type: ignore
        self._sender.sendTexture(tex_id, gl.GL_TEXTURE_2D, SPOUT_SIZE, SPOUT_SIZE, False, 0) # type: ignore
        gl.glDeleteTextures([tex_id]) # type: ignore
