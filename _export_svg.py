"""Drive archify's own SVG exporter headlessly and write the result out."""

import base64

import os
import re
import tempfile
import subprocess
import sys
from pathlib import Path

import os as _os

CHROME = Path(_os.environ.get(
    "CHROME_PATH",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
))
ROOT = Path(__file__).resolve().parent

HOOK = """
<script>
(function () {
  var b64 = null, err = null, done = false;
  try {
    var nativeCreate = URL.createObjectURL,
      window.__blobById = {};
    var captureId = 'bt' + Date.now();
    var L = /svg/;
    URL.createObjectURL = function (blob) {
      if (blob && L.test(blob.type || '')) {
        var id = captureId;
        window.__blobById[id] = blob;
        try {
          var u = nativeCreate.call(URL, blob);
          if (u) {
            var a = document.createElement('a');
            a.href = u;
            a.download = 'x.svg';
            a.dataset._blobId = id;
            document.body.appendChild(a);
            try { a.click(); } catch (e) {}
            a.remove();
          }
        } catch (e) {}
      }
      return nativeCreate.call(URL, blob);
    };
    var btn = document.querySelector('[data-format="svg"]');
    if (!btn) { err = new Error('no svg export control'); throw err; }
    btn.click();
    setTimeout(function () {
      document.documentElement.setAttribute('data-export-done','1');
    }, 9000);
  } catch (e) { err = e; }
  window._arch_export_done = function () {
    if (!done) {
      done = true;
      if (err) {
        var el = document.createElement('pre');
        el.id = '__svg_err';
        el.textContent = String(err.stack || err);
        document.body.appendChild(el);
      }
      var id = captureId;
      if (window.__blobById && window.__blobById[id]) {
        setTimeout(function () {
          try {
            var fr = new FileReader();
            fr.onload = function () {
              b64 = fr.result;
              document.documentElement.setAttribute('data-export-done','1');
            };
            fr.onerror = function () {
              window.__err2 = new Error('fr error');
            };
            fr.readAsDataURL(window.__blobById[id]);
          } catch (e2) {
            window.__err2 = e2;
          }
        }, 20);
      } else {
        setTimeout(function () {
          document.documentElement.setAttribute('data-export-done','1');
        }, 30);
      }
    }
  };
})();
</script>
"""

# Fallback extractor: if the archify Blob-download path does not materialize in
# headless chrome, serialize the rendered diagram SVG directly via the DOM.
FALLBACK_HOOK = """
<script>
(function () {
  function tryExtract() {
    try {
      var btn = document.querySelector('[data-format="svg"]');
      if (!btn) {
        var el = document.createElement('pre');
        el.id = '__svg_probe_no_button';
        el.textContent = 'no svg export control';
        document.body.appendChild(el);
        document.documentElement.setAttribute('data-export-done','1');
        return;
      }
      btn.click();
    } catch (e) {
      var el = document.createElement('pre');
      el.id = '__svg_probe_throw';
      el.textContent = String(e.stack || e);
      document.body.appendChild(el);
      document.documentElement.setAttribute('data-export-done','1');
      return;
    }
    var done = false;
    var timer = setInterval(function () {
      if (done) return;
      var svgEl = document.querySelector('svg[data-layout-contract]');
      if (!svgEl) {
        if (Date.now() > 25000) {
          clearInterval(timer);
          var el2 = document.createElement('pre');
          el2.id = '__svg_probe_no_svg';
          el2.textContent = 'diagram svg did not appear';
          document.body.appendChild(el2);
          document.documentElement.setAttribute('data-export-done','1');
        }
        return;
      }
      done = true;
      clearInterval(timer);
      var ser = new XMLSerializer();
      var text = ser.serializeToString(svgEl);
      var el = document.createElement('pre');
      el.id = '__svg_b64';
      el.textContent = btoa(unescape(encodeURIComponent(text)));
      document.body.appendChild(el);
      document.documentElement.setAttribute('data-export-done','1');
    }, 150);
    setTimeout(function () {
      if (!done) {
        clearInterval(timer);
        var el3 = document.createElement('pre');
        el3.id = '__svg_probe_timeout';
        el3.textContent = 'timed out waiting for diagram svg';
        document.body.appendChild(el3);
        document.documentElement.setAttribute('data-export-done','1');
      }
    }, 25000);
  }
  tryExtract();
})();
</script>
"""


def export_svg(html_path: Path, out_svg: Path) -> int:
    try:
        svg = _resolve_svg_from_html(html_path)
    except RuntimeError as e:
        print("ERROR:", str(e)[:2000])
        return 1
    out_svg.write_text(svg, encoding="utf-8")
    return 0


def _chrome_dump(html_uri: str, out_path: Path, virtual_time_budget: int,
                     timeout: int) -> str:
    """Run chrome headless dump-dom against `html_uri` and return the serialized
    DOM text. Writes to `out_path` and returns its text on success."""
    try:
        proc = subprocess.run(
            [
                str(CHROME),
                "--headless=new",
                "--disable-gpu",
                "--virtual-time-budget=" + str(virtual_time_budget),
                "--dump-dom",
                html_uri,
            ],
            stdout=open(out_path, "wb"),
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        pass
    if not out_path.exists():
        return ""
    return out_path.read_text(encoding="utf-8", errors="replace")


def _b64_from_dom(dom_text: str) -> str | None:
    m = re.search(r'<pre id="__svg_b64">([\s\S]*?)</pre>', dom_text)
    return m.group(1).strip() if m else None


def _err_from_dom(dom_text: str) -> tuple[str, str] | None:
    for err_id in ('__svg_err', '__svg_probe_throw', '__svg_probe_no_button',
                   '__svg_probe_no_svg', '__svg_probe_timeout'):
        m = re.search(r'<pre id="' + err_id + r'">([\s\S]*?)</pre>', dom_text)
        if m:
            return err_id, m.group(1).strip()
    return None


def _resolve_svg_from_html(html_path: Path) -> str:
    """Resolve the diagram SVG markup from an archify HTML file without leaving
    probe artifacts in the working tree. Uses the blob-download path first and
    falls back to direct DOM serialization if chrome never emits the b64 tag."""
    src = html_path.read_text(encoding="utf-8")
    tmpdir = tempfile.mkdtemp(prefix="_arch_export_")
    try:
        td = Path(tmpdir)
        dom_path = td / "dom.html"
        hook_path = td / "hook.html"

        hook_path.write_text(
            src.replace("</body>", HOOK + "</body>", 1), encoding="utf-8"
        )
        dom = _chrome_dump(
            hook_path.resolve().as_uri(), dom_path,
            virtual_time_budget=28000, timeout=260,
        )
        b64 = _b64_from_dom(dom)
        err = _err_from_dom(dom)
        if err:
            raise RuntimeError("archify export hook error: " + err[0] + ": " +
                               err[1][:2000])
        if not b64:
            hook_path.write_text(
                src.replace("</body>", FALLBACK_HOOK + "</body>", 1),
                encoding="utf-8",
            )
            dom = _chrome_dump(
                hook_path.resolve().as_uri(), dom_path,
                virtual_time_budget=30000, timeout=60,
            )
            b64 = _b64_from_dom(dom)
            err = _err_from_dom(dom)
            if err:
                raise RuntimeError("archify fallback hook error: " + err[0] +
                                   ": " + err[1][:2000])
            if not b64:
                raise RuntimeError(
                    "no svg payload from archify html; dom len " + str(len(dom)))
        return base64.b64decode(b64).decode("utf-8")
    finally:
        try:
            hook_path.unlink(missing_ok=True)
            dom_path.unlink(missing_ok=True)
            os.rmdir(td)
        except OSError:
            pass


if __name__ == "__main__":
    html = Path(sys.argv[1])
    out = Path(sys.argv[2])
    code = export_svg(html, out)
    if code == 0:
        svg = out.read_text(encoding="utf-8")
        print(f"{out.name}: {len(svg)} chars, has_xmlns={'xmlns' in svg[:600]}, "
              f"styles={svg.count('<style')}, bg={'#020617' in svg[:4000]}")
    sys.exit(code)
