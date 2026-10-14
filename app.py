import os, sys, re, glob, tempfile, subprocess
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="강의 소리 ➔ 텍스트 메모장", page_icon="📝", layout="centered")
st.title("📝 강의 소리 ➔ 텍스트 모장")
st.caption("아이패드14 브루투스 이어패드 연결 상태에서도 서보가 접 음성을 텍스트로 환합니다.")

if "memo" not in st.session_state:
      st.session_state.memo = ""

def ensure_sr():
      try:
                import speech_recognition as sr
                return sr
except ModuleNotFoundError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "SpeechRecognition", "audioop-lts", "standard-aifc", "standard-chunk"], check=False)
        import speech_recognition as sr
        return sr

def transcribe_file(path):
      sr = ensure_sr()
      r = sr.Recognizer()
      with tempfile.TemporaryDirectory() as tmpdir:
                chunk_pattern = os.path.join(tmpdir, "chunk_%03d.wav")
                subprocess.run([
                    "ffmpeg", "-y", "-i", path,
                    "-vn", "-ac", "1", "-ar", "16000",
                    "-f", "segment", "-segment_time", "30",
                    "-c:a", "pcm_s16le", chunk_pattern
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                wavs = sorted(glob.glob(os.path.join(tmpdir, "chunk_*.wav")))
                if not wavs:
                              return ""
                          out = []
                bar = st.progress(0, text="음성 변환 중...")
                for i, w in enumerate(wavs):
                              try:
                                                with sr.AudioFile(w) as src:
                                                                      audio_data = r.record(src)
                                                                      txt = r.recognize_google(audio_data, language="ko-KR")
                                                                      if txt.strip():
                                                                                                out.append(txt.strip())
                              except Exception:
                                                pass
                                            bar.progress((i + 1) / len(wavs), text=f"음성 환 중... ({i+1}/{len(wavs)})")
                          bar.empty()
                return "\n\n".join(out)

  url = st.text_input("1. 웹 강의 음성 주소(URL) 입력", placeholder="유튜브 또는 MP4 음성 주소 넣어놓기")
up = st.file_uploader("또는 아이패드 음성/음성 파일 선", type=["mp4", "mov", "m4a", "mp3", "wav"])

if url.strip():
      st.video(url.strip())
elif up:
      st.video(up)

if st.button("🎯 음성 소리  텍스트로 변하기", type="primary", use_container_width=True):
      if not url.strip() and not up:
                st.warning("먼저 음성 주소를 력하거나 파일을 선택해 주세요.")
else:
          with st.spinner("소리를 텍스트로 변환하고 있습니다..."):
                        try:
                                          if up:
                                                                ext = os.path.splitext(up.name)[1] or ".mp4"
                                                                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as t:
                                                                                          t.write(up.read())
                                                                                          p = t.name
                                                                                      txt = transcribe_file(p)
                                                                if os.path.exists(p):
                                                                                          os.remove(p)
                                          else:
                                                                import yt_dlp
                                                                m = re.search(r"(?:v=|/|youtu\.be/|embed/|shorts/)([0-9A-Za-z_-]{11})", url)
                                                                txt = ""
                                                                if m:
                                                                                          try:
                                                                                                                        from youtube_transcript_api import YouTubeTranscriptApi
                                                                                                                        vid = m.group(1)
                                                                                                                        if hasattr(YouTubeTranscriptApi, "get_transcript"):
                                                                                                                                                          tr = YouTubeTranscriptApi.get_transcript(vid, languages=["ko", "en"])
                                                                                                                                                          txt = "\n".join(x["text"] for x in tr)
                                                                                            else:
                                fetched = YouTubeTranscriptApi().fetch(vid, languages=["ko", "en"])
                                                                            txt = "\n".join(snippet.text for snippet in fetched)
except Exception:
                            pass
                    if not txt:
                                              with tempfile.TemporaryDirectory() as d:
                                                                            opts = {"format": "bestaudio/best", "outtmpl": os.path.join(d, "a.%(ext)s"), "quiet": True, "noplaylist": True}
                                                                            with yt_dlp.YoutubeDL(opts) as ydl:
                                                                                                              info = ydl.extract_info(url.strip(), download=True)
                                                                                                              txt = transcribe_file(ydl.prepare_filename(info))
                                                                                              if txt.strip():
                                                                                                                    st.session_state.memo = (st.session_state.memo + "\n\n" + txt.strip()).strip()
                                                                                                                    st.success("변환 완료! 아래에서 해 워드에 붙여넣으세요.")
                                                else:
                    st.warning("인식된 음성이 없습니다.")
except Exception as e:
                st.error(f"변환 오류: {e}")

st.session_state.memo = st.text_area("2. 변환된 텍 메모장", value=st.session_state.memo, height=240)

esc = st.session_state.memo.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
components.html(f"""<button id="b" style="width:100%;height:50px;background:#10b981;color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:800;cursor:pointer;">📋 전체 텍스트 복사하기 (워드 붙여넣기)</button><script>document.getElementById("b").onclick = async () => {{ const t = `{esc}`; try {{ await navigator.clipboard.writeText(t); }} catch(e) {{ const a = document.createElement("textarea"); a.value = t; document.body.appendChild(a); a.select(); document.execCommand("copy"); document.body.removeChild(a); }} document.getElementById("b").textContent = "☑ 복사 완료! 워드 앱에 붙여넣으세요"; }};</script>""", height=65)
