from flask import Flask, request, render_template
from funasr import AutoModel
import os
import ffmpeg

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化 Paraformer 模型
model = AutoModel(
    model="paraformer-zh", model_revision="v2.0.4",
    vad_model="fsmn-vad", vad_model_revision="v2.0.4",
    punc_model="ct-punc-c", punc_model_revision="v2.0.4",
    spk_model="cam++", spk_model_revision="v2.0.2"
)

# 转换音频为 WAV 格式
def convert_to_wav(input_path, output_path):
    try:
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(stream, output_path, format="wav", acodec="pcm_s16le", ar=16000)
        ffmpeg.run(stream, overwrite_output=True)
    except ffmpeg.Error as e:
        raise Exception(f"音频转换失败: {e}")

# 处理转录结果，按说话人分组（您的函数）
def process_transcript(res):
    sorted_res = sorted(res, key=lambda x: x['timestamp'][0])
    turns = []
    current_speaker = None
    current_text = []
    for item in sorted_res:
        speaker = item.get('speaker', 'Unknown')
        text = item['text']
        if speaker == current_speaker:
            current_text.append(text)
        else:
            if current_speaker is not None:
                turns.append({'speaker': current_speaker, 'text': ' '.join(current_text)})
            current_speaker = speaker
            current_text = [text]
    if current_speaker is not None:
        turns.append({'speaker': current_speaker, 'text': ' '.join(current_text)})
    return turns

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 检查文件上传
        if "audio" not in request.files:
            return "未上传音频文件", 400
        audio_file = request.files["audio"]
        if audio_file.filename == "":
            return "未选择文件", 400

        # 保存上传文件
        input_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
        audio_file.save(input_path)

        # 转换为 WAV
        output_path = os.path.join(UPLOAD_FOLDER, "converted.wav")
        convert_to_wav(input_path, output_path)

        # 生成转录结果
        res = model.generate(input=output_path, batch_size_s=600, hotword="充电桩")
        turns = process_transcript(res)

        # 清理临时文件
        os.remove(input_path)
        os.remove(output_path)

        # 返回网页，带转录结果
        return render_template("index.html", turns=turns, filename=res[0]["key"])
    return render_template("index.html", turns=None, filename=None)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 locally
    app.run(debug=False, host="0.0.0.0", port=port)