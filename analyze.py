import librosa
import numpy as np
import json
import os

# 配置：歌曲文件夹路径
SONGS_DIR = "songs"
# 输出的歌单列表文件
PLAYLIST_FILE = "playlist.json"

def analyze_song(filepath, output_path):
    print(f"   -> 正在分析: {filepath} ...")
    try:
        # 加载音频
        y, sr = librosa.load(filepath, sr=22050, mono=True)
        # 提取音高
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), 
                                                     fmax=librosa.note_to_hz('C6'), sr=sr)
        times = librosa.times_like(f0, sr=sr)
        melody_data = []
        
        # 降采样并保存 (每隔3个点存一次，减小体积)
        step = 3
        for i in range(0, len(f0), step):
            pitch = f0[i]
            if not np.isnan(pitch):
                melody_data.append({
                    "t": round(float(times[i]), 2),
                    "p": round(float(pitch), 1)
                })
        
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(melody_data, f)
        return True
    except Exception as e:
        print(f"   !!! 分析失败: {e}")
        return False

def main():
    # 确保文件夹存在
    if not os.path.exists(SONGS_DIR):
        os.makedirs(SONGS_DIR)
        print(f"创建了文件夹 '{SONGS_DIR}'，请把MP3放进去！")
        return

    # 获取当前目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    songs_dir_abs = os.path.join(base_dir, SONGS_DIR)
    
    playlist = []
    
    files = [f for f in os.listdir(songs_dir_abs) if f.lower().endswith('.mp3')]
    print(f"发现 {len(files)} 首歌曲，开始批量处理...")

    for filename in files:
        mp3_path = os.path.join(songs_dir_abs, filename)
        json_filename = os.path.splitext(filename)[0] + ".json"
        json_path = os.path.join(songs_dir_abs, json_filename)
        
        # 如果json不存在，才去分析（避免重复跑）
        if not os.path.exists(json_path):
            success = analyze_song(mp3_path, json_path)
        else:
            print(f"   -> 已存在跳过: {filename}")
            success = True
            
        if success:
            # 加入歌单列表
            playlist.append({
                "name": os.path.splitext(filename)[0], # 歌名 (去后缀)
                "mp3": f"{SONGS_DIR}/{filename}",      # 相对路径
                "json": f"{SONGS_DIR}/{json_filename}" # 相对路径
            })

    # 保存歌单列表
    playlist_path = os.path.join(base_dir, PLAYLIST_FILE)
    with open(playlist_path, "w", encoding='utf-8') as f:
        json.dump(playlist, f, ensure_ascii=False, indent=2)
    
    print("\n--------------------------------")
    print(f"全部搞定！歌单已生成: {PLAYLIST_FILE}")
    print("现在可以打开网页 K 歌了！")

if __name__ == "__main__":
    main()