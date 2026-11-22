import asyncio, os, subprocess, wave, sys
import imageio_ffmpeg
import edge_tts

OUT = r"E:\vscode\zhouji\webHome\_video\audio"
os.makedirs(OUT, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()

VOICE = "zh-CN-YunjianNeural"

SEGS = {
    "s1": "物业做账是不是很头疼？收费、报修、停车、访客记录分散在好几本本子里，月底对账对不上，欠费催缴没记录，工单跟进混乱，费时又容易出错！",
    "s2": "试试物管通单机物业系统！一套房号串联全部业务，收费、欠费、报修、停车、访客全部绑定房屋档案。首页看板实时查看收费率、待办工单；欠费自动分级催缴，每一条催缴记录全程留痕；报修工单从登记、派单到完工闭环跟进；访客、车位台账统一管理；系统自动生成统计报表，数据实时联动，不用反复核对Excel。单机本地部署，数据保存在本机，断网离线也能用，一次付费永久使用！",
    "s3": "适合中小物业公司、自管小区、安置房、商铺公寓使用！对比纸质台账、Excel、云端物业系统，不用每年续费，不依赖网络，本地数据安全可控。",
    "s4": "想要了解更多功能，欢迎访问官网咨询！",
}

RATE = sys.argv[1] if len(sys.argv) > 1 else "+0%"
TAG = sys.argv[2] if len(sys.argv) > 2 else "r0"


def dur_of(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


async def main():
    lines = [f"rate={RATE} tag={TAG}"]
    total = 0.0
    for k, text in SEGS.items():
        mp3 = os.path.join(OUT, f"{k}_{TAG}.mp3")
        wav = os.path.join(OUT, f"{k}_{TAG}.wav")
        comm = edge_tts.Communicate(text, VOICE, rate=RATE)
        await comm.save(mp3)
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", mp3, "-ar", "44100", "-ac", "1", wav], check=True)
        d = dur_of(wav)
        total += d
        lines.append(f"{k}: {len(text)} chars -> {d:.2f}s  ({len(text)/d:.2f} chars/s)")
    lines.append(f"TOTAL: {total:.2f}s")
    with open(r"E:\vscode\zhouji\webHome\_tts_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

asyncio.run(main())
