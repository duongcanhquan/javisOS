// ============================================
// JAVIS OS - Voice Layer (Web Speech API)
// ============================================

class JavisVoice {
  constructor(opts = {}) {
    this.lang = opts.lang || "vi-VN";
    this.onTranscript = opts.onTranscript || (() => {});
    this.onInterim = opts.onInterim || (() => {});
    this.onStart = opts.onStart || (() => {});
    this.onEnd = opts.onEnd || (() => {});
    this.onError = opts.onError || (() => {});

    this.recognition = null;
    this.synth = window.speechSynthesis;
    this.isListening = false;
    // Nhớ lựa chọn bật/tắt đọc qua reload. MẶC ĐỊNH TẮT: người dùng mới vào phải im lặng,
    // chỉ đọc thành tiếng khi họ tự bật công tắc (lưu "1" vào localStorage).
    this.ttsEnabled = (localStorage.getItem("javis.ttsEnabled") === "1");
    this.vietnameseVoice = null;

    // Edge TTS backend (server)
    this.ttsBackend = opts.ttsBackend || "/tts"; // "/tts" hoặc null để dùng browser
    this.ttsVoice = opts.ttsVoice || "vi-VN-HoaiMyNeural"; // nhãn UI: Ngọc Thu (nữ) | Nam Minh (nam)
    this.ttsRate = opts.ttsRate || "+25%";
    this.currentAudio = null;
    this.ttsQueue = [];
    this.speechQueue = [];   // hàng đợi đọc nối tiếp (các bước trung gian + kết quả)
    this._streamBuf = "";    // gom mẩu stream thành câu rồi mới đọc, khỏi ngắt giữa chữ
    this._liveAudios = [];   // audio đang phát (có thể chồng đuôi ~70ms cho liền mạch)
    this.isPlaying = false;
    this._resumeAfterTTS = false;  // mic đang mở khi TTS bắt đầu → đọc xong tự mở nghe lại
    this._resumeTimer = null;

    // Audio analysis - cho hiệu ứng phát sáng theo âm thanh
    this.audioCtx = null;
    this.outAnalyser = null;   // âm Javis đọc (TTS)
    this.inAnalyser = null;    // âm mic (khi nghe)
    this.micStream = null;
    this._freqData = new Uint8Array(64);

    this._initRecognition();
    this._loadVoices();
  }

  _ensureCtx() {
    if (!this.audioCtx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AC();
    }
    if (this.audioCtx.state === "suspended") this.audioCtx.resume();
    return this.audioCtx;
  }

  _stopMicMeter() {
    // Trả mic cho SpeechRecognition. getUserMedia đang giữ track thì Chrome nhận dạng
    // vẫn "chạy" nhưng không nghe được giọng - đúng triệu chứng bấm mic, nói, im.
    if (this.micStream) {
      try { this.micStream.getTracks().forEach((t) => t.stop()); } catch (e) {}
      this.micStream = null;
    }
    this.inAnalyser = null;
  }

  async _startMicMeter() {
    const ctx = this._ensureCtx();
    if (!this.micStream) {
      this.micStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
      });
    }
    if (this.inAnalyser) return;
    const src = ctx.createMediaStreamSource(this.micStream);
    const an = ctx.createAnalyser();
    an.fftSize = 128;
    src.connect(an);
    this.inAnalyser = an;
  }

  getInputLevel() {
    if (!this.inAnalyser || !this.isListening) return 0;
    this.inAnalyser.getByteFrequencyData(this._freqData);
    let s = 0;
    for (let i = 0; i < this._freqData.length; i++) s += this._freqData[i];
    return Math.min(1, (s / this._freqData.length) / 200);
  }

  getOutputLevel() {
    if (!this.outAnalyser) return 0;
    this.outAnalyser.getByteFrequencyData(this._freqData);
    let s = 0;
    for (let i = 0; i < this._freqData.length; i++) s += this._freqData[i];
    return Math.min(1, (s / this._freqData.length) / 180);
  }

  getLevel() {
    return Math.max(this.getInputLevel(), this.getOutputLevel());
  }

  _initRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      console.warn("Trình duyệt không hỗ trợ SpeechRecognition. Dùng Chrome hoặc Edge.");
      return;
    }
    if (this.recognition) {
      try {
        this.recognition.onend = null;
        this.recognition.onerror = null;
        this.recognition.onresult = null;
        this.recognition.onstart = null;
        this.recognition.abort();
      } catch (e) {}
    }

    this.recognition = new SR();
    this.recognition.lang = this.lang;
    this.recognition.continuous = true;       // nghe liên tục, không dừng giữa câu
    this.recognition.interimResults = true;
    this.recognition.maxAlternatives = 1;

    this.accumulatedTranscript = "";
    this.userStopped = false;                 // user chủ động dừng?
    this.silenceMs = 1500;                    // im lặng bao lâu thì tự gửi
    this._silenceTimer = null;

    this.recognition.onstart = () => {
      this._starting = false;
      this.isListening = true;
      this.userStopped = false;
      this.accumulatedTranscript = "";
      this.onStart();
      clearTimeout(this._hearHint);
      this._hearHint = setTimeout(() => {
        if (this.isListening && !this.accumulatedTranscript) {
          this.onInterim("Chưa nghe được giọng. Nói gần mic hơn, cho phép microphone, và mở bằng Chrome/Edge tại http://127.0.0.1:7777 (đừng dùng cửa sổ xem trong Cursor).");
        }
      }, 4000);
    };

    this.recognition.onresult = (event) => {
      // Chỉ bỏ kết quả khi loa đang phát THẬT. Cờ synth.speaking của Chrome hay kẹt true
      // sau cancel() → nuốt hết giọng user, không hiện chữ, không gửi.
      if (this.isSpeaking()) return;
      let interim = "", final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += transcript;
        else interim += transcript;
      }
      if (final) this.accumulatedTranscript += final + " ";
      const display = (this.accumulatedTranscript + interim).trim();
      if (display) {
        this.onInterim(display);
        clearTimeout(this._hearHint);
        clearTimeout(this._silenceTimer);
        this._silenceTimer = setTimeout(() => this.stopListening(), this.silenceMs);
      }
    };

    this.recognition.onerror = (event) => {
      const err = event.error;
      if (err === "no-speech") return;
      if (err === "aborted") return;
      this._starting = false;
      this.isListening = false;
      if (err === "audio-capture") {
        this._stopMicMeter();
      }
      this.onError(err);
    };

    this.recognition.onend = () => {
      this._starting = false;
      if (!this.userStopped) {
        try {
          this.recognition.start();
          return;
        } catch (e) {}
      }
      this.isListening = false;
      const finalText = this.accumulatedTranscript.trim();
      if (finalText) this.onTranscript(finalText);
      else if (this.userStopped) this.onInterim("");
      this.onEnd();
    };
  }

  _loadVoices() {
    const load = () => {
      const voices = this.synth.getVoices();
      // Tìm giọng Vietnamese tốt nhất theo thứ tự ưu tiên
      this.vietnameseVoice =
        voices.find(v => v.lang === "vi-VN" && v.name.includes("Google")) ||
        voices.find(v => v.lang === "vi-VN") ||
        voices.find(v => v.lang.startsWith("vi")) ||
        null;
    };
    load();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = load;
    }
  }

  startListening() {
    if (!this.recognition) {
      this._initRecognition();
      if (!this.recognition) { this.onError("not-supported"); return; }
    }
    if (this.isListening || this._starting) return;
    this._starting = true;
    this._resumeAfterTTS = false;
    clearTimeout(this._resumeTimer);
    this.synth.cancel();
    this.stopSpeaking();
    // Trả mic + start() NGAY trong cử chỉ bấm. Await getUserMedia rồi mới start thì Chrome
    // coi như hết cử chỉ, nhận dạng không thu được tiếng.
    this._stopMicMeter();
    try {
      this.recognition.start();
    } catch (e) {
      try {
        this._initRecognition();
        this.recognition.start();
      } catch (e2) {
        this._starting = false;
        this.onError("start-failed: " + (e2 && e2.message || e.message));
      }
    }
  }

  stopListening() {
    clearTimeout(this._silenceTimer);
    clearTimeout(this._hearHint);
    this._starting = false;
    this._resumeAfterTTS = false;
    clearTimeout(this._resumeTimer);
    if (this.recognition && this.isListening) {
      this.userStopped = true;
      this.recognition.stop();
    }
  }

  toggleListening() {
    if (this.isListening) this.stopListening();
    else this.startListening();
  }

  // Đọc NGAY: ngắt phần đang đọc + xoá hàng đợi, rồi đọc đoạn này.
  // opts.force = đọc kể cả khi đang tắt tiếng (dùng cho nút "nghe thử giọng").
  speak(text, opts = {}) {
    this.stopSpeaking();
    this.enqueueSpeak(text, opts);
  }

  // Đọc NỐI TIẾP: thêm vào cuối hàng đợi, KHÔNG cắt ngang đoạn đang đọc.
  // Dùng cho các cập nhật ở bước trung gian (stream).
  enqueueSpeak(text, opts = {}) {
    if (!this.ttsEnabled && !opts.force) return;
    const clean = this._cleanForTTS(text);
    if (!clean) return;
    // Đang đọc: nối vào hàng chunk hiện tại và tải sẵn, khỏi ngắt mỗi câu một lần HTTP.
    if (this.isPlaying && this.ttsChunks && this.ttsChunks.length) {
      if (this._awaitingMore) {
        this.ttsChunks.push(clean);
        this._awaitingMore = false;
        this._playChunk(this.ttsChunks.length - 1);
        return;
      }
      const i = this._chunkIndex == null ? 0 : this._chunkIndex;
      if (this.ttsChunks.length > i + 1) {
        const lastI = this.ttsChunks.length - 1;
        this.ttsChunks[lastI] = this.ttsChunks[lastI] + " " + clean;
        if (this._preloaded && this._preloaded.i === lastI) {
          this._revoke(this._preloaded.audio);
          this._preloaded = null;
        }
      } else {
        this.ttsChunks.push(clean);
      }
      const nextI = (this._chunkIndex == null ? 0 : this._chunkIndex) + 1;
      const next = this.ttsChunks[nextI] || "";
      if (next.length >= 360) this._prefetch(nextI);
      return;
    }
    this.speechQueue.push(clean);
    if (!this.isPlaying) this._pumpQueue();
  }

  // Stream token: gom thành cụm ~550 ký tự rồi mới gọi TTS.
  // Tách từng câu là nguyên nhân đọc xong dòng 1 rồi im vài giây chờ Edge TTS câu sau.
  feedStream(raw, opts = {}) {
    if (!this.ttsEnabled && !opts.force) return;
    this._streamOpen = true;
    this._streamBuf += (raw || "");
    this._drainStream(false, opts);
  }

  flushStream(opts = {}) {
    this._streamOpen = false;
    this._drainStream(true, opts);
  }

  _drainStream(force, opts) {
    const clean = this._cleanForTTS(this._streamBuf || "");
    if (!clean) { if (force) this._streamBuf = ""; return; }
    if (force) {
      this._streamBuf = "";
      this.enqueueSpeak(clean, opts);
      return;
    }
    const started = this.isPlaying || (this.speechQueue && this.speechQueue.length)
      || (this.ttsChunks && this.ttsChunks.length);
    if (!started) {
      // Câu đầu đọc ngay. Đợi 500 ký tự thì user nghe thấy "cực chậm".
      const sent = clean.match(/^[\s\S]{16,160}?[.!?…]["'\)]*(?:\s+|$)/);
      if (sent) {
        this._streamBuf = clean.slice(sent[0].length);
        this.enqueueSpeak(sent[0].trim(), opts);
        return;
      }
      if (clean.length < 90) return;
      const n = this._cutChunk(clean, 70, 140);
      this._streamBuf = clean.slice(n);
      this.enqueueSpeak(clean.slice(0, n).trim(), opts);
      return;
    }
    if (clean.length < 480) return;
    const n = this._cutChunk(clean, 400, 800);
    this._streamBuf = clean.slice(n);
    this.enqueueSpeak(clean.slice(0, n).trim(), opts);
  }

  _cutChunk(s, min, max) {
    const window = s.slice(0, Math.min(max, s.length));
    const find = (re) => {
      re.lastIndex = 0;
      let m, last = -1;
      while ((m = re.exec(window)) !== null) {
        if (m.index + m[0].length >= min) last = m.index + m[0].length;
      }
      return last;
    };
    let p = find(/[.!?…]["'\)]*\s+/g);
    if (p < min) p = find(/[,;:]\s+/g);
    if (p < min) p = find(/\s+/g);
    if (p < min) p = s.length <= max ? s.length : max;
    return p;
  }

  // Chỉ true khi loa đang phát THẬT. isPlaying còn bật lúc chờ Edge TTS (vài giây) - nếu
  // dùng cờ đó thì mic tưởng Javis đang nói nên bỏ hết giọng user.
  isSpeaking() {
    const a = this.currentAudio;
    if (a && !a.paused && !a.ended) return true;
    // Chỉ tin speechSynthesis khi đang đi đường giọng máy (không có Edge TTS).
    // Chrome hay để speaking=true sau cancel() → nuốt hết kết quả nhận dạng.
    if (!this.ttsBackend && this.synth && this.synth.speaking) return true;
    return false;
  }

  // Lấy đoạn kế trong hàng đợi để đọc; hết hàng đợi thì dừng.
  _pumpQueue() {
    if (!this.speechQueue || this.speechQueue.length === 0) {
      if (this._streamOpen) {
        this._awaitingMore = true;
        this.isPlaying = true;
        return;
      }
      this.isPlaying = false;
      this._awaitingMore = false;
      this._stopBargeMonitor();
      this._resumeRecognitionIfNeeded();             // đọc xong hết → mở nghe lại nếu trước đó mic đang mở
      return;
    }
    this.isPlaying = true;
    this._muteRecognition();
    this._startBargeMonitor();
    // Gộp cả hàng đợi thành MỘT lượt TTS. Mỗi câu một request là nguyên nhân đọc 1 dòng rồi nghỉ lâu.
    const text = this.speechQueue.splice(0).join(" ");
    if (this.ttsBackend) this._speakBackend(text);   // Edge TTS (giọng Việt chuẩn)
    else this._speakBrowser(text);                   // fallback Web Speech
  }

  // Javis bắt đầu đọc mà mic đang nghe → tạm NGỪNG nhận dạng (abort, bỏ kết quả dở),
  // vì SpeechRecognition sẽ chép chính giọng TTS thành tin nhắn của user. Ngắt lời bằng
  // giọng vẫn hoạt động - barge-in đo mức âm qua luồng mic đã khử vọng, không cần nhận dạng.
  _muteRecognition() {
    if (!this.recognition || !this.isListening) return;
    this._resumeAfterTTS = true;
    this.userStopped = true;             // chặn auto-restart trong onend
    clearTimeout(this._silenceTimer);
    this.accumulatedTranscript = "";     // bỏ những gì lỡ nghe - không gửi
    this.onInterim("");                  // xoá chữ đang hiện dở trên màn hình
    try { this.recognition.abort(); } catch (e) {}
  }

  // Đọc xong (hoặc bị dừng) → mở nghe lại nếu mic từng bị tạm ngừng vì TTS.
  // Chờ một nhịp cho đuôi âm tắt hẳn; phiên nhận dạng MỚI nên không dính giọng TTS cũ.
  _resumeRecognitionIfNeeded() {
    if (!this._resumeAfterTTS) return;
    this._resumeAfterTTS = false;
    clearTimeout(this._resumeTimer);
    this._resumeTimer = setTimeout(() => {
      if (!this.isPlaying && !this.isListening) this.startListening();
    }, 180);
  }

  // ---- Ngắt lời (barge-in): đang đọc mà nghe user nói đủ to/đủ lâu → dừng đọc + mở nghe ngay ----
  _startBargeMonitor() {
    // Ngắt lời chỉ khi user THỰC SỰ dùng giọng (đã cấp mic). Đo BIÊN ĐỘ SÓNG (time-domain RMS) từ
    // luồng mic ĐÃ khử vọng - đúng độ TO thật, đáng tin hơn trung bình phổ (bị pha loãng bởi dải tần
    // cao im lặng nên giọng nói không bao giờ chạm ngưỡng). Tự HIỆU CHỈNH theo nền (echo + ồn) đo
    // trong ~600ms đầu để hợp mọi máy/môi trường, hạn chế tự-ngắt do nghe lại chính giọng TTS.
    if (this._bargeTimer) return;
    if (!this.micStream || !this.inAnalyser) {
      this._startMicMeter().then(() => {
        if (this.isPlaying) this._startBargeMonitor();
      }).catch(() => {});
      return;
    }
    const N = this.inAnalyser.fftSize || 128;
    if (!this._timeData || this._timeData.length !== N) this._timeData = new Uint8Array(N);
    let hits = 0, ticks = 0, baseline = 0;
    this._bargeTimer = setInterval(() => {
      if (!this.isPlaying) { this._stopBargeMonitor(); return; }
      this.inAnalyser.getByteTimeDomainData(this._timeData);
      let s = 0;
      for (let k = 0; k < N; k++) { const dv = this._timeData[k] - 128; s += dv * dv; }
      const rms = Math.sqrt(s / N) / 128;   // 0..1 (im lặng ~0.005, nói thường ~0.05-0.2)
      ticks++;
      if (ticks <= 6) { baseline = Math.max(baseline, rms); return; }   // ~600ms đầu: đo nền/echo
      const thresh = Math.max(0.045, baseline * 2 + 0.02);             // vượt HẲN nền mới coi là user nói
      if (rms > thresh) { if (++hits >= 3) { this._stopBargeMonitor(); this._bargeIn(); } }   // ~300ms liên tục
      else hits = 0;
    }, 100);
  }

  _stopBargeMonitor() {
    if (this._bargeTimer) { clearInterval(this._bargeTimer); this._bargeTimer = null; }
  }

  _bargeIn() {
    this.stopSpeaking();       // dừng đọc ngay (không để chồng tiếng)
    this.startListening();     // user muốn nói → mở nghe luôn, bắt trọn câu
  }

  _cleanForTTS(text) {
    return text
      .replace(/```[\s\S]*?```/g, " ")        // bỏ code block
      .replace(/\*\*(.+?)\*\*/g, "$1")
      .replace(/\*(.+?)\*/g, "$1")
      .replace(/`(.+?)`/g, "$1")
      .replace(/!\[.*?\]\(.*?\)/g, "")          // ảnh
      .replace(/\[(.+?)\]\(.+?\)/g, "$1")       // link → giữ chữ
      .replace(/^#{1,6}\s+/gm, "")              // heading
      .replace(/^\s*\d+[.)]\s+/gm, "")          // list số
      .replace(/^\s*[-*•]\s+/gm, "")            // list dấu đầu dòng
      .replace(/\s*[\u2014\u2013]\s*/g, ", ")   // gạch ngang em/en (U+2014/2013) -> phẩy (hết khựng khi đọc)
      .replace(/\s*\|\s*/g, ", ")               // ô bảng markdown
      .replace(/\n{2,}/g, ". ")                 // đoạn mới → chấm
      .replace(/\n/g, ", ")                     // xuống dòng → phẩy (liền mạch, vẫn có nhịp thở)
      .replace(/\s*([,.])\s*([,.])/g, "$1")     // dồn dấu trùng (.,  ,. → .)
      .replace(/\s{2,}/g, " ")
      .trim();
  }

  _chunkUrl(text) {
    return `${this.ttsBackend}?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(this.ttsVoice)}&rate=${encodeURIComponent(this.ttsRate)}`;
  }

  _revoke(audio) {
    if (!audio) return;
    try { audio.pause(); } catch (e) {}
    if (audio._blobUrl) {
      try { URL.revokeObjectURL(audio._blobUrl); } catch (e) {}
      audio._blobUrl = null;
    }
  }

  async _loadAudio(text, retry) {
    const url = this._chunkUrl(text) + (retry ? "&retry=1" : "");
    const res = await fetch(url);
    if (!res.ok) throw new Error("tts " + res.status);
    const blob = await res.blob();
    const obj = URL.createObjectURL(blob);
    const audio = new Audio(obj);
    audio._blobUrl = obj;
    audio.preload = "auto";
    return audio;
  }

  _prefetch(j) {
    if (!this.ttsChunks || j == null || j >= this.ttsChunks.length) return;
    if (this._preloaded && this._preloaded.i === j && this._preloaded.audio) return;
    const text = this.ttsChunks[j];
    const token = this._chunkToken;
    this._loadAudio(text).then((audio) => {
      if (token !== this._chunkToken || !this.isPlaying || !this.ttsChunks || this.ttsChunks[j] !== text) {
        this._revoke(audio);
        return;
      }
      if (this._preloaded && this._preloaded.i === j && this._preloaded.audio !== audio) {
        this._revoke(this._preloaded.audio);
      }
      this._preloaded = { i: j, audio };
      if (this._pendingNext && this._pendingNext.i === j) {
        const go = this._pendingNext.go;
        this._pendingNext = null;
        go();
      }
    }).catch(() => {});
  }

  _speakBackend(text) {
    // Câu đầu ngắn → loa ra sớm. Phần còn lại cụm lớn, tải SONG SONG lúc đang đọc câu đầu.
    this.ttsChunks = this._splitHeadThenRest(text);
    this._preloaded = null;
    this._awaitingMore = false;
    this._chunkIndex = 0;
    this.isPlaying = true;
    this._prefetch(1);
    this._playChunk(0);
  }

  _splitHeadThenRest(text) {
    if (!text) return [];
    if (text.length <= 150) return [text];
    const n = this._cutChunk(text, 50, 140);
    const head = text.slice(0, n).trim();
    const rest = text.slice(n).trim();
    const chunks = head ? [head] : [];
    if (rest) chunks.push(...this._splitIntoChunks(rest, 720));
    return chunks.filter(Boolean);
  }

  _playChunk(i, retry) {
    // Hết chunk: nếu stream còn đổ chữ thì giữ loa, đừng khép lượt (khép rồi mở lại = nghỉ lâu).
    if (!this.ttsChunks || i >= this.ttsChunks.length) {
      if (this._streamOpen || (this._streamBuf && this._streamBuf.trim())) {
        this._awaitingMore = true;
        return;
      }
      this._pumpQueue();
      return;
    }
    this._chunkIndex = i;
    this._chunkToken = (this._chunkToken || 0) + 1;
    const token = this._chunkToken;
    this._prefetch(i + 1);
    const pre = (!retry && this._preloaded && this._preloaded.i === i) ? this._preloaded.audio : null;
    if (pre) this._preloaded = null;

    const start = (audio) => {
      if (token !== this._chunkToken || !this.isPlaying) { this._revoke(audio); return; }
      this.currentAudio = audio;

      try {
        const ctx = this._ensureCtx();
        if (ctx && ctx.state === "running" && !audio.__routed) {
          audio.crossOrigin = "anonymous";
          const src = ctx.createMediaElementSource(audio);
          const an = ctx.createAnalyser();
          an.fftSize = 128;
          src.connect(an);
          an.connect(ctx.destination);
          this.outAnalyser = an;
          audio.__routed = true;
        }
      } catch (e) { /* phát thẳng vẫn ổn */ }

      this._prefetch(i + 1);

      let handled = false;
      const onFail = () => {
        if (handled || token !== this._chunkToken) return;
        handled = true;
        audio.onerror = null;
        this._chunkFailed(i, retry);
      };
      const goNext = (force) => {
        if (handled || token !== this._chunkToken) return;
        const j = i + 1;
        const nextReady = this._preloaded && this._preloaded.i === j && this._preloaded.audio
          && this._preloaded.audio.readyState >= 2;
        if (!force && this.ttsChunks && j < this.ttsChunks.length && !nextReady) {
          this._pendingNext = { i: j, go: () => goNext(true) };
          this._prefetch(j);
          return;
        }
        handled = true;
        this._pendingNext = null;
        audio.onended = null;
        audio.ontimeupdate = null;
        this._playChunk(j);
      };
      audio.addEventListener("ended", () => {
        this._liveAudios = (this._liveAudios || []).filter((a) => a !== audio);
        this._revoke(audio);
      });
      audio.onended = () => goNext(false);
      audio.ontimeupdate = () => {
        if (!audio.duration || !isFinite(audio.duration)) return;
        const next = this._preloaded && this._preloaded.i === i + 1 && this._preloaded.audio;
        const ready = next && next.readyState >= 3;
        if (ready && audio.duration - audio.currentTime < 0.12) goNext(true);
      };
      audio.onerror = onFail;
      this._liveAudios.push(audio);
      audio.play().catch(onFail);
    };

    if (pre) start(pre);
    else this._loadAudio(this.ttsChunks[i], retry).then(start).catch(() => {
      if (token !== this._chunkToken) return;
      this._chunkFailed(i, retry);
    });
  }

  // Đoạn TTS backend lỗi: thử LẠI backend 1 lần (lỗi mạng chốc lát) để GIỮ giọng Việt;
  // vẫn hỏng thì TUYỆT ĐỐI không rơi về giọng mặc định (thường là tiếng Anh) khi đang đọc tiếng Việt -
  // đó chính là "giọng Anh lạ chèn giữa chừng". Có giọng đúng ngôn ngữ trong máy thì đọc, không thì BỎ đoạn.
  _chunkFailed(i, retry) {
    if (!this.ttsChunks || i >= this.ttsChunks.length) { this._pumpQueue(); return; }
    if (!retry) { this._playChunk(i, true); return; }
    const okBrowserVoice = this.lang.startsWith("vi") ? !!this.vietnameseVoice : true;
    if (okBrowserVoice) this._speakBrowser(this.ttsChunks[i], () => this._playChunk(i + 1));
    else this._playChunk(i + 1);
  }

  // onDone: gọi khi đọc xong đoạn (mặc định: lấy đoạn kế trong hàng đợi).
  _speakBrowser(text, onDone) {
    const done = onDone || (() => this._pumpQueue());
    const chunks = this._splitIntoChunks(text, 200);
    let idx = 0;
    const playNext = () => {
      if (idx >= chunks.length) { done(); return; }
      const utter = new SpeechSynthesisUtterance(chunks[idx++]);
      utter.lang = this.lang;
      if (this.vietnameseVoice) utter.voice = this.vietnameseVoice;
      utter.rate = 1.25;
      utter.onend = playNext;
      utter.onerror = playNext;
      this.synth.speak(utter);
    };
    playNext();
  }

  stopSpeaking() {
    this._chunkToken = (this._chunkToken || 0) + 1;
    this._streamOpen = false;
    this._awaitingMore = false;
    this._pendingNext = null;
    this._stopBargeMonitor();
    this.synth.cancel();
    this._streamBuf = "";
    (this._liveAudios || []).forEach((a) => { try { a.pause(); a.onended = null; a.ontimeupdate = null; this._revoke(a); } catch (e) {} });
    this._liveAudios = [];
    if (this.currentAudio) {
      this._revoke(this.currentAudio);
      this.currentAudio = null;
    }
    if (this._preloaded && this._preloaded.audio) this._revoke(this._preloaded.audio);
    this._preloaded = null;
    this._chunkIndex = null;
    this.ttsChunks = null;
    this.ttsQueue = [];
    this.speechQueue = [];
    this.isPlaying = false;
    this._resumeRecognitionIfNeeded();   // mic từng bị tạm ngừng vì TTS → mở nghe lại
  }

  setVoice(voiceName) {
    this.ttsVoice = voiceName;
  }

  setRate(rate) {
    this.ttsRate = rate;
  }

  setRecognitionLang(lang) {
    this.lang = lang;
    if (this.recognition) this.recognition.lang = lang;
  }

  toggleTTS() {
    this.ttsEnabled = !this.ttsEnabled;
    try { localStorage.setItem("javis.ttsEnabled", this.ttsEnabled ? "1" : "0"); } catch (e) {}
    if (!this.ttsEnabled) this.stopSpeaking();
    return this.ttsEnabled;
  }

  _splitIntoChunks(text, maxLen) {
    const sentences = text.match(/[^.!?]+[.!?]+|\s*[^.!?]+$/g) || [text];
    const chunks = [];
    let current = "";
    for (const s of sentences) {
      if ((current + s).length > maxLen && current) {
        chunks.push(current.trim());
        current = s;
      } else {
        current += s;
      }
    }
    if (current.trim()) chunks.push(current.trim());
    return chunks.filter(c => c.length > 0);
  }

  isSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }
}

window.JavisVoice = JavisVoice;
