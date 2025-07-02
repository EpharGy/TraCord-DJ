# pyright: reportAttributeAccessIssue=false
import threading
import time
import traceback
import SpoutGL
from PIL import Image

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
    def __init__(self, sender_name="TraCordDJ CoverArt", width=150, height=150):
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
            glfw.destroy_window(self._window)
            glfw.terminate()
        self._sender = None
        self._window = None

    def send_pil_image(self, pil_img):
        if not self._running:
            return
        with self._lock:
            self._pending_img = pil_img.copy()

    def _run(self):
        try:
            if not glfw.init():
                print("[SpoutGL] Failed to init GLFW")
                return
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
            self._window = glfw.create_window(self.width, self.height, "SpoutGL Hidden", None, None)
            if not self._window:
                print("[SpoutGL] Failed to create GLFW window")
                glfw.terminate()
                return
            glfw.make_context_current(self._window)
            self._sender = SpoutSender()
            self._sender.setSenderName(self.sender_name)
            self._ready.set()
            while self._running:
                img = None
                with self._lock:
                    if self._pending_img is not None:
                        img = self._pending_img
                        self._pending_img = None
                if img is not None:
                    self._send_image(img)
                time.sleep(0.02)
        except Exception as e:
            print(f"[SpoutGL] Error in sender thread: {e}\n{traceback.format_exc()}")
        finally:
            self._sender = None
            if self._window:
                glfw.destroy_window(self._window)
                glfw.terminate()

    def _send_image(self, pil_img):
        img = pil_img.convert("RGBA").resize((self.width, self.height))
        img_bytes = img.tobytes()
        # Upload to OpenGL texture
        tex_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_bytes)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        self._sender.sendTexture(tex_id, gl.GL_TEXTURE_2D, self.width, self.height, False, 0)
        gl.glDeleteTextures([tex_id])
