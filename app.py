import os, re, tempfile
import streamlit as st
import streamlit.components.v1 as components
from pydub import AudioSegment
import speech_recognition as sr
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

st.set_page_config(page_title="강 소리 → 텍스트 메모장", page_icon="📝", layout="centered")
st.title("📝 강의 소리 → 텍스트 메모장")
st.caption("아이폰14 블루투스 이어폰 연결 상태에서도 서버가 직접 영상 소리를 텍스트로 변환합니다.")

if "memo" not in st.session_state:
      st.session_state.memo = ""

def transcribe_file(path):
      r = sr.Recognizer()
      audio = AudioSegment.from_file(path).set_channels(1).set_frame_rate(16000)
      chunks = [audio[i:i+30000] for i in range(0, len(audio), 30000)]
      out = []
      bar = st.progress(0, text="음성 변환 중...")
      for i, c in enumerate(chunks):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                              c.export(f.name, format="wav")
                              w = f.name
                          try:
                                        with sr.AudioFile(w) as src:
                                                          out.append(r.recognize_google(r.record(src), language="ko-KR"))
                          except Exception:
                                        pass
finally:
            if os.path.exists(w):
                              os.remove(w)
                      bar.progress((i + 1) / len(chunks))
    bar.empty()
    return "\n\n".join(out)

url = st.text_input("1. 웹 강의 영상 주소(URL) 입력", placeholder="유튜브 또는 MP4 영상 주소 붙여넣기")
up = st.file_uploader("또는 아이폰 영상/음성 파 선택", type=["mp4", "mov", "m4a", "mp3", "wav"])

if url.strip():
      st.video(url.strip())
elif up:
    st.video(up)

if st.button("🎯 영상 소리 → 텍스트로 변환하기", type="primary", use_container_width=True):
      with st.spinner("소리를 텍스트로 변환하고 있습니다..."):
                try:
                              if up:
                                                ext = os.path.splitext(up.name)[-1] or ".mp4"
                                                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as t:
                                                                      t.write(up.read())
                                                                      p = t.name
                                                                  txt = transcribe_file(p)
                                                os.remove(p)
                else:
                                  m = re.search(r"(?:v=|\/|youtu\.be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})", url)
                                  txt = ""
                                  if m:
                                                        try:
                                                                                  tr = YouTubeTranscriptApi.get_transcript(m.group(1), languages=["ko", "en"])
                                                                                  txt = "\n".join(x["text"] for x in tr)
                except Exception:
                                pass
                        if not txt:
                                              with tempfile.TemporaryDirectory() as d:
                                                                        opts = {"format": "bestaudio/best", "outtmpl": os.path.join(d, "a.%(ext)s"), "quiet": True}
                                                                        with yt_dlp.YoutubeDL(opts) as ydl:
                                                                                                      info = ydl.extract_info(url.strip(), download=True)
                                                                                                      txt = transcribe_file(ydl.prepare_filename(info))
                                                                                      if txt.strip():
                                                                                                        st.session_state.memo = (st.session_state.memo + "\n\n" + txt.strip()).strip()
                                                                                                        st.success("변환 완료! 아래에서 복사 워드에 붙여넣으세요.")
                                                else:
                st.warning("인식된 음성이 없습니다.")
except Exception as e:
            st.error(f"변환 오류: {e}")

st.session_state.memo = st.text_area("2. 변환된 텍스트 메모장", value=st.session_state.memo, height=240)

esc = st.session_state.memo.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
components.html(f"""
<button id="b" style="width:100%;height:50px;background:#10b981;color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:800;cursor:pointer;">📋 전체 텍스트 복사하기 (워드 붙여넣기)</button>
<script>
document.getElementById('b').onclick = async () => {{
  const t = `{esc}`;
    try {{ await navigator.clipboard.writeText(t); }} catch(e) {{
        const a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select(); document.execCommand('copy'); document.body.removeChild(a);
          }}
            document.getElementById('b').textContent = '✅ 복사 완! 워드 앱에 붙여넣으세요';
            }};
            </script>
            """, height=65)
