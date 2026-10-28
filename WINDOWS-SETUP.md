# Windows-এ Claude Code দিয়ে ভিডিও এডিট: setup গাইড

এই গাইড একবারই করতে হবে, সব মিলিয়ে প্রায় ৩০–৪৫ মিনিট লাগবে। এরপর শুধু ধাপ ৮ থেকে কাজ।

**যা লাগবে:** Windows 10 বা 11, ইন্টারনেট, আর Claude-এর paid plan (Pro বা Max)। আপনি এখন যে account-এ Claude Code ব্যবহার করছেন, সেটাই চলবে।

**PowerShell কী:** Start মেনুতে `PowerShell` লিখে **Windows PowerShell** খুলুন। এটা একটা কালো বা নীল জানালা, যেখানে command লিখে **Enter** চাপতে হয়। নিচে যেখানেই command দেওয়া আছে, সেটা কপি করে PowerShell-এ paste করবেন (right-click করলেই paste হয়), তারপর Enter।

---

## ধাপ ১: Git install
1. https://git-scm.com/download/win খুলুন। Download নিজে থেকে শুরু হবে।
2. ফাইলটা চালান আর সব জায়গায় **Next** চাপুন। কিছু বদলানোর দরকার নেই।

*কেন লাগে:* GitHub থেকে আপনার repo নামানোর জন্য। Claude Code-ও Windows-এ এটা ব্যবহার করে।

## ধাপ ২: Python install
1. https://www.python.org/downloads/ খুলে হলুদ **Download Python** বোতাম চাপুন।
2. ফাইলটা চালান। প্রথম পর্দার নিচে **"Add python.exe to PATH"** বক্সে অবশ্যই টিক দিন। তারপর **Install Now** চাপুন।

*কেন লাগে:* আমাদের সব এডিটিং script Python-এ লেখা।

## ধাপ ৩: ffmpeg install
PowerShell-এ লিখুন:
```
winget install Gyan.FFmpeg
```
"Agree" জাতীয় প্রশ্ন এলে `Y` লিখে Enter চাপুন। শেষ হলে **PowerShell বন্ধ করে আবার খুলুন**।

*কেন লাগে:* ভিডিও কাটা, জোড়া আর export করার মূল টুল।

## ধাপ ৪: Claude Code install
PowerShell-এ লিখুন:
```
irm https://claude.ai/install.ps1 | iex
```
শেষ হলে PowerShell বন্ধ করে আবার খুলুন। তারপর দেখুন ঠিকমতো install হয়েছে কিনা:
```
claude --version
```
একটা version নম্বর দেখালেই ঠিক আছে।

## ধাপ ৫: আপনার repo নামান
```
cd $HOME\Documents
git clone https://github.com/creator-hossain/site
cd site
```
- GitHub login চাইলে browser খুলবে। আপনার GitHub account দিয়ে login করুন।
- এখন **Documents\site** folder-এ সব আছে: script, font, পুরনো ভিডিও আর skill।

## ধাপ ৬: Claude Code চালু করুন
একই PowerShell-এ (`site` folder-এর ভিতরে থেকে):
```
claude
```
- প্রথমবার browser খুলে Claude account-এ login চাইবে। Login করে PowerShell-এ ফিরে আসুন।
- "Do you trust this folder?" জিজ্ঞেস করলে **Yes** দিন।

## ধাপ ৭: Claude-কে দিয়ে বাকি setup করান
Claude-এর ঘরে লিখুন:
> video-edit skill-এর setup check চালাও, আর কোনো FIX থাকলে ঠিক করো।

Claude নিজে বাকি কাজগুলো করবে:
- দরকারি Python package install করবে।
- AI model (প্রায় ১৭৫MB) নামাবে।
- ffmpeg আর বাংলা লেখার ব্যবস্থা পরীক্ষা করবে।

কোনো command চালানোর আগে অনুমতি চাইলে **Yes** দিন। শেষে `ALL GOOD` দেখালে setup শেষ।

**বাংলা লেখা নিয়ে একটা কথা:** Windows-এ বাংলা যুক্তাক্ষর ঠিকভাবে দেখাতে Pillow-এর একটা অতিরিক্ত লাইব্রেরি (FriBiDi) লাগে। এটা Windows-এ আগে থেকে পরীক্ষা করা যায়নি। Setup check এখানে `FIX` দেখালে Claude skill-এর নির্দেশনা অনুযায়ী ঠিক করবে। তাতেও না হলে WSL (Windows-এর ভিতরে Linux) ব্যবহারের পথ আছে, Claude বলে দেবে।

---

## ধাপ ৮: প্রতিবার ভিডিও এডিট করা (setup-এর পর শুধু এটুকু)
1. PowerShell খুলে লিখুন:
   ```
   cd $HOME\Documents\site
   claude
   ```
2. আপনার ফুটেজ আর reference ভিডিও একটা folder-এ রাখুন, যেমন `Downloads`।
3. Claude-কে লিখুন, যেমন:
   > `C:\Users\<আপনার নাম>\Downloads\footage.mp4` আমার ভিডিও, আর `C:\Users\<আপনার নাম>\Downloads\ref.mp4` reference। এই reference-এর মতো same style-এ এডিট করো। Project-এর নাম `corolla2`।

   Path সহজে পেতে: File Explorer-এ ফাইলে **Shift + right-click** দিয়ে **"Copy as path"** বেছে paste করুন।
4. Claude skill অনুযায়ী এই কাজগুলো করবে:
   - Reference বিশ্লেষণ।
   - আপনার ভিডিওর frame, mask আর শব্দের সময় বের করা।
   - কয়েকটা **preview ছবি** বানানো (ঠিকানা বলে দেবে, Explorer-এ খুলে দেখবেন)।
5. Preview দেখে বলুন "ঠিক আছে" বা কী বদলাতে হবে। তারপর পুরো ভিডিও আর sound বানাবে।
6. Final ভিডিও থাকবে `Documents\site\video-pipeline\<project নাম>\` folder-এ।
7. ভালো লাগলে বলুন: **"commit আর push করো"**। এতে script আর style GitHub-এ জমা থাকবে, পরে "corolla2-এর স্টাইলে করো" বললেই হবে।

## পরামর্শ
- Voice-এর লেখা (transcript বা SRT) থাকলে সেটাও দিন। তাহলে বাংলা caption-এর সময় অনেক নির্ভুল হবে।
- ৪০ সেকেন্ডের ভিডিওতে mask আর render মিলিয়ে সাধারণ কম্পিউটারে প্রায় ২০–৪০ মিনিট লাগতে পারে। এই সময়ে কম্পিউটার বন্ধ করবেন না।
- কোথাও আটকে গেলে PowerShell-এর লেখাটা কপি করে Claude-কে দিন, ও ঠিক করে দেবে।
