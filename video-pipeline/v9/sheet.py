import sys
from PIL import Image
pre, ts, out = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
ims = [Image.open(f"{pre}_{t}.png").resize((240, 427)) for t in ts]
c = Image.new("RGB", (240 * min(5, len(ims)), 427 * ((len(ims) + 4) // 5)))
for i, im in enumerate(ims): c.paste(im, ((i % 5) * 240, (i // 5) * 427))
c.save(out)
