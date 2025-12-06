import os
import json
import librosa
import numpy as np
import parselmouth 
from concurrent.futures import ProcessPoolExecutor

# 配置
SONGS_DIR = "songs"
PLAYLIST_FILE = "playlist.json"

def analyze_song_fast(args):
    filepath, output_path, filename = args
    
    # 1. 检查是否存在
    if os.path.exists(output_path):
        return f" -> [跳过] 已存在: {filename}"

    try:
        # 2. 加载音频 (使用 librosa 读取，因为它的兼容性最好)
        # 采样率设为 16000 足够分析人声，速度快
        y, sr = librosa.load(filepath, sr=16000, mono=True)

        # 3. 核心黑科技：转换成 Praat Sound 对象
        snd = parselmouth.Sound(y, sampling_frequency=sr)

        # 4. 提取音高 (To Pitch)
        # pitch_floor=50Hz, pitch_ceiling=800Hz (人声范围)
        # time_step=0.05 (每 50ms 取一个点，减少 JSON 体积)
        pitch = snd.to_pitch(time_step=0.05, pitch_floor=50.0, pitch_ceiling=800.0)
        
        # 5. 提取数据
        pitch_values = pitch.selected_array['frequency']
        pitch_times = pitch.xs()
        
        melody_data = []
        
        # 遍历并清洗数据 (0 就是没声音)
        for t, p in zip(pitch_times, pitch_values):
            if p > 0: # Praat 用 0 表示无声/无音高
                melody_data.append({
                    "t": round(float(t), 2), 
                    "p": round(float(p), 1)  # 保留1位小数，极大压缩体积
                })

        # 6. 保存
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(melody_data, f)
            
        return f" -> [极速完成] {filename}"

    except Exception as e:
        return f" !!! [失败] {filename}: {e}"

def main():
    if not os.path.exists(SONGS_DIR):
        os.makedirs(SONGS_DIR)
        print("请放入 MP3 文件！")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    songs_dir_abs = os.path.join(base_dir, SONGS_DIR)
    
    files = [f for f in os.listdir(songs_dir_abs) if f.lower().endswith('.mp3')]
    print(f"发现 {len(files)} 首歌曲，启动 Praat 引擎...")

    playlist = []
    tasks = []

    for filename in files:
        mp3_path = os.path.join(songs_dir_abs, filename)
        json_filename = os.path.splitext(filename)[0] + ".json"
        json_path = os.path.join(songs_dir_abs, json_filename)
        
        playlist.append({
            "name": os.path.splitext(filename)[0],
            "mp3": f"{SONGS_DIR}/{filename}",
            "json": f"{SONGS_DIR}/{json_filename}"
        })
        tasks.append((mp3_path, json_path, filename))

    # 多进程并行
    with ProcessPoolExecutor() as executor:
        for res in executor.map(analyze_song_fast, tasks):
            print(res)

    with open(os.path.join(base_dir, PLAYLIST_FILE), "w", encoding='utf-8') as f:
        json.dump(playlist, f, ensure_ascii=False, indent=2)

    print("\n搞定！速度是原来的 100 倍。")

if __name__ == "__main__":
    main()
