/**
 * Công việc → Tạo video: workbench wizard full màn (không timeline).
 * Mỗi tab = một kiểu video; form gọn, lời gần gũi; phải = bước + kết quả.
 * Thời lượng kéo tới 10 phút; số slide + yêu cầu theo từng pipeline (shotcraft/paper/…).
 */
(function () {
  "use strict";

  var MAX_DURATION_SEC = 600; /* 10 phút */

  var DEFAULT_ASPECTS = [
    { value: "9:16", label: "Dọc điện thoại (Reels/TikTok)" },
    { value: "1:1", label: "Vuông" },
    { value: "16:9", label: "Ngang (YouTube)" },
  ];

  var FEATURES = [
    {
      id: "postcard",
      pipeline: "postcard-video",
      label: "Promo cinematic",
      blurb: "Shotcraft · 157 thẻ shot + SFX/BGM",
      full: "Promo cinematic (video-shotcraft)",
      when: "Promo / launch / demo UI sản phẩm: recipe shot Remotion, chụp trang thật, SFX/BGM.",
      example: "Ra mắt app ghi chú → clip ~30s dọc, mode tự do hoặc template Ink Press.",
      time: "Gợi ý 15–45s (template ~36s); kéo tối đa 10 phút",
      topicPh: "Ví dụ: Ra mắt app ghi chú cho học sinh",
      needsUrl: true,
      assetsLabel: "URL sản phẩm / staging hoặc screenshot *",
      assetsHint: "Shotcraft cần trang thật hoặc ảnh chụp - không bịa UI.",
      assetsPh: "https://… hoặc đường dẫn ảnh đã có",
      caps: [
        "3 mode (template / tự do / cùng làm)",
        "157 shot card + gallery",
        "2.5D camera + beat-sync",
        "SFX 16 nhóm + BGM đôi bản",
        "Workbench + xuất Jianying",
      ],
      aspects: DEFAULT_ASPECTS,
      duration: {
        min: 10,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 30,
        hint: "Postcard khuyến nghị 15–45s. >60s chậm/tốn; tối đa kéo 10 phút.",
      },
      slides: {
        min: 3,
        max: 24,
        step: 1,
        def: 6,
        label: "Số shot / khung hình",
        hint: "Mỗi shot một động tác chính (quy tắc shotcraft: một shot = một động tác).",
      },
      extras: [
        {
          group: "Mode shotcraft",
          id: "vidShotMode",
          type: "select",
          label: "Cách làm",
          def: "tự do",
          options: [
            { value: "template Ink Press", label: "Template Ink Press (đổi sản phẩm)" },
            { value: "tự do", label: "Tự do - Javis quyết hết" },
            { value: "cùng sáng tạo", label: "Cùng làm - dừng duyệt từng bước" },
          ],
        },
        {
          id: "vidShotFamily",
          type: "select",
          label: "Ưu tiên nhóm shot (gallery)",
          def: "tự chọn",
          options: [
            { value: "tự chọn", label: "Tự chọn từ 157 thẻ" },
            { value: "opening", label: "Mở đầu & thương hiệu" },
            { value: "typography", label: "Chữ & title card" },
            { value: "ui-entrance", label: "UI đăng trường / showcase" },
            { value: "camera", label: "Vận máy & không gian" },
            { value: "data", label: "Số liệu & chỉ số" },
            { value: "interaction", label: "Tương tác / demo tính năng" },
            { value: "transition", label: "Chuyển cảnh" },
            { value: "rhythm", label: "Nhịp / montage" },
            { value: "effects", label: "Ánh sáng & nhấn" },
            { value: "outro", label: "Kết / CTA" },
          ],
        },
        {
          id: "vidShotCards",
          type: "text",
          label: "Tên shot card cụ thể (tuỳ chọn)",
          def: "",
          ph: "vd: deck-deal-flyin, row-embed, spotlight-hero-card",
        },
        {
          group: "Hình & chuyển động",
          id: "vidCapture",
          type: "select",
          label: "Chụp trang sản phẩm",
          def: "full-page 2x",
          options: [
            { value: "full-page 2x", label: "Full page 2x (khuyến nghị)" },
            { value: "viewport", label: "Chỉ viewport" },
            { value: "đã có screenshot", label: "Dùng ảnh sẵn (không crawl)" },
          ],
        },
        {
          id: "vidCamEnergy",
          type: "select",
          label: "Cường độ vận máy / motion",
          def: "vừa",
          options: [
            { value: "nhẹ", label: "Nhẹ / chậm, nhiều hold" },
            { value: "vừa", label: "Vừa (mặc định shotcraft)" },
            { value: "cao", label: "Cao năng / trailer" },
          ],
        },
        {
          id: "vidTextOnScreen",
          type: "select",
          label: "Chữ trên hình",
          def: "ít",
          options: [
            { value: "không", label: "Không chữ" },
            { value: "ít", label: "Ít (headline / title card)" },
            { value: "nhiều", label: "Nhiều caption" },
          ],
        },
        {
          group: "Âm thanh",
          id: "vidBgm",
          type: "select",
          label: "Nhạc nền (BGM)",
          def: "xuất cả hai",
          options: [
            { value: "có", label: "Có BGM" },
            { value: "không", label: "Không BGM" },
            { value: "xuất cả hai", label: "Xuất cả bản có + không BGM" },
          ],
        },
        {
          id: "vidBeatSync",
          type: "select",
          label: "Khóa nhịp BGM (beat-sync)",
          def: "có nếu có BGM",
          options: [
            { value: "có nếu có BGM", label: "Có - cắt/động theo beat" },
            { value: "không", label: "Không khóa nhịp" },
          ],
        },
        {
          id: "vidSfx",
          type: "select",
          label: "SFX (149 mẫu / 16 nhóm)",
          def: "vừa",
          options: [
            { value: "ít", label: "Ít" },
            { value: "vừa", label: "Vừa (riser→impact→sparkle)" },
            { value: "nhiều", label: "Nhiều / đậm" },
            { value: "không", label: "Không SFX" },
          ],
        },
        {
          id: "vidVoiceFile",
          type: "select",
          label: "Voiceover",
          def: "không",
          options: [
            { value: "không", label: "Không VO (mặc định shotcraft)" },
            { value: "file đính kèm", label: "Dùng file VO đính kèm" },
            { value: "cần TTS thêm", label: "Cần TTS (làm tay trong Remotion)" },
          ],
        },
        {
          group: "Sau khi xong",
          id: "vidWorkbench",
          type: "select",
          label: "Workbench chỉnh sau render",
          def: "có",
          options: [
            { value: "có", label: "Mở workbench (chỉnh chữ/màu/tốc độ)" },
            { value: "không", label: "Không cần" },
          ],
        },
        {
          id: "vidJianying",
          type: "select",
          label: "Xuất dự án Jianying (CapCut CN)",
          def: "không",
          options: [
            { value: "không", label: "Không" },
            { value: "có", label: "Có - để tự sửa tiếp" },
          ],
        },
      ],
    },
    {
      id: "short-vo",
      pipeline: "pixcelvideo",
      label: "Có lời đọc",
      blurb: "Ảnh từng cảnh + Edge-TTS",
      full: "Video có lời đọc (pixcelvideo)",
      when: "Clip giải thích / bán hàng: bắt buộc ảnh mỗi cảnh + giọng đọc.",
      example: "Máy lọc nước → 45 giây có lời thoại và phụ đề.",
      time: "Kéo tới 10 phút; số cảnh chia theo lời",
      topicPh: "Ví dụ: Vì sao nên dùng máy lọc nước",
      needsUrl: false,
      assetsLabel: "Link / ảnh tham khảo (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Có thì dán, không có cũng được",
      caps: [
        "Ảnh bắt buộc từng cảnh",
        "ChatGPT hoặc Pollinations",
        "Edge-TTS + phụ đề",
        "Pixelle RunningHub (tuỳ chọn)",
      ],
      aspects: [
        { value: "9:16", label: "Dọc / portrait" },
        { value: "1:1", label: "Vuông" },
        { value: "16:9", label: "Ngang / landscape" },
      ],
      duration: {
        min: 15,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 45,
        hint: "30–90s thường đủ. Dài hơn = nhiều cảnh/lời (tối đa 10 phút).",
      },
      slides: {
        min: 3,
        max: 40,
        step: 1,
        def: 6,
        label: "Số cảnh (slide ảnh)",
        hint: "Mỗi cảnh = 1 ảnh + 1 đoạn lời. Thiếu ảnh → lỗi, không ra video chữ trơn.",
      },
      extras: [
        {
          group: "Ảnh",
          id: "vidImageSource",
          type: "select",
          label: "Nguồn ảnh cảnh",
          def: "ChatGPT rồi Pollinations",
          options: [
            { value: "ChatGPT rồi Pollinations", label: "ChatGPT (ưu tiên) → Pollinations" },
            { value: "chỉ ChatGPT", label: "Chỉ ChatGPT OAuth" },
            { value: "chỉ Pollinations", label: "Chỉ Pollinations" },
            { value: "ảnh đính kèm", label: "Dùng ảnh đính kèm theo thứ tự cảnh" },
          ],
        },
        {
          id: "vidRequireImages",
          type: "select",
          label: "Bắt buộc có ảnh",
          def: "có",
          options: [
            { value: "có", label: "Có - thiếu ảnh thì dừng (khuyến nghị)" },
            { value: "không", label: "Không - cho phép thiếu (không khuyến nghị)" },
          ],
        },
        {
          id: "vidPixelle",
          type: "select",
          label: "Pixelle / RunningHub",
          def: "tự động nếu có",
          options: [
            { value: "tự động nếu có", label: "Dùng nếu API sống, không thì fallback" },
            { value: "không", label: "Không dùng Pixelle" },
            { value: "bắt buộc", label: "Bắt buộc Pixelle" },
          ],
        },
        {
          group: "Giọng & chữ",
          id: "vidVoice",
          type: "select",
          label: "Giọng đọc (Edge-TTS)",
          def: "tự chọn",
          options: [
            { value: "tự chọn", label: "Javis tự chọn theo ngôn ngữ" },
            { value: "nữ", label: "Ưu tiên giọng nữ" },
            { value: "nam", label: "Ưu tiên giọng nam" },
          ],
        },
        {
          id: "vidPace",
          type: "select",
          label: "Tốc độ đọc",
          def: "vừa",
          options: [
            { value: "chậm", label: "Chậm, rõ" },
            { value: "vừa", label: "Vừa" },
            { value: "nhanh", label: "Nhanh, năng động" },
          ],
        },
        {
          id: "vidCaptions",
          type: "select",
          label: "Phụ đề / chữ overlay",
          def: "có",
          options: [
            { value: "có", label: "Có phụ đề trên hình" },
            { value: "không", label: "Không phụ đề" },
          ],
        },
        {
          id: "vidHookCta",
          type: "select",
          label: "Cấu trúc lời",
          def: "Hook → Ý → CTA",
          options: [
            { value: "Hook → Ý → CTA", label: "Hook → Ý chính → CTA" },
            { value: "chỉ giải thích", label: "Chỉ giải thích" },
            { value: "bán hàng mạnh", label: "Bán hàng (pain → offer → CTA)" },
          ],
        },
      ],
    },
    {
      id: "collage",
      pipeline: "paperdesign",
      label: "Collage Vox",
      blurb: "Paperdesign · theme + beat + VO",
      full: "Video collage giấy (paperdesign / Vox)",
      when: "Explainer kiểu cắt dán báo: beat map, theme bake-off, poster → motion → VO/BGM.",
      example: "Lạm phát là gì? → collage ~45s, theme swiss-modern.",
      time: "Số poster = số beat; kéo tới 10 phút",
      topicPh: "Ví dụ: Lạm phát giải thích ngắn",
      needsUrl: false,
      assetsLabel: "Ảnh neo / A-roll / tài liệu (tuỳ chọn)",
      assetsHint: "C-roll: ảnh chân dung hoặc sản phẩm để neo sticker.",
      assetsPh: "Ảnh sản phẩm, logo, clip talking-head…",
      caps: [
        "9 theme preset + bake-off",
        "Narrative arc (PAS/AIDA…)",
        "Motion calm/punchy/max",
        "TTS xAI + BGM Minimax",
        "C-roll / A-roll / local engine",
      ],
      aspects: [
        { value: "9:16", label: "9:16 dọc" },
        { value: "1:1", label: "1:1 vuông" },
        { value: "16:9", label: "16:9 ngang" },
        { value: "3:4", label: "3:4" },
      ],
      duration: {
        min: 20,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 45,
        hint: "30s→6–8 beat; 60s→10–12. Tối đa 10 phút.",
      },
      slides: {
        min: 3,
        max: 30,
        step: 1,
        def: 6,
        label: "Số beat / poster",
        hint: "Mỗi beat ≈ 1 poster; mỗi beat thường tách 2 shot (wide + detail).",
      },
      extras: [
        {
          group: "Nhìn (LOOK)",
          id: "vidPaperTheme",
          type: "select",
          label: "Theme collage",
          def: "bake-off rồi chọn",
          options: [
            { value: "bake-off rồi chọn", label: "Bake-off 4 theme rồi chọn" },
            { value: "american-retro", label: "american-retro" },
            { value: "swiss-modern", label: "swiss-modern" },
            { value: "punk-zine", label: "punk-zine" },
            { value: "atomic-age", label: "atomic-age" },
            { value: "soviet-constructivist", label: "soviet-constructivist" },
            { value: "wpa-propaganda", label: "wpa-propaganda" },
            { value: "70s-groovy", label: "70s-groovy" },
            { value: "chinese-ink", label: "chinese-ink" },
            { value: "newsprint-editorial", label: "newsprint-editorial" },
          ],
        },
        {
          id: "vidArc",
          type: "select",
          label: "Cấu trúc kể (narrative arc)",
          def: "hook_payoff",
          options: [
            { value: "hook_payoff", label: "hook_payoff (mặc định)" },
            { value: "pas", label: "PAS - pain / agitate / solve" },
            { value: "bab", label: "BAB - before / after / bridge" },
            { value: "aida", label: "AIDA" },
            { value: "storybrand", label: "storybrand" },
            { value: "how_it_works", label: "how_it_works" },
            { value: "timeline", label: "timeline" },
            { value: "listicle", label: "listicle" },
            { value: "myth_buster", label: "myth_buster" },
            { value: "three_act", label: "three_act" },
          ],
        },
        {
          id: "vidMotionStyle",
          type: "select",
          label: "Biên độ motion",
          def: "punchy",
          options: [
            { value: "calm", label: "calm" },
            { value: "punchy", label: "punchy (mặc định nhiều theme)" },
            { value: "max", label: "max" },
          ],
        },
        {
          group: "Giọng & phụ đề",
          id: "vidPaperVoice",
          type: "select",
          label: "Giọng TTS (xAI)",
          def: "vi-Mai",
          options: [
            { value: "vi-Mai", label: "Mai (nữ, Việt)" },
            { value: "vi-Duc", label: "Duc (nam, Việt)" },
            { value: "vi-Minh", label: "Minh (nam, Việt)" },
            { value: "leo", label: "Leo (đa ngôn ngữ, mặc định skill)" },
            { value: "ara", label: "Ara (nữ, đa ngôn ngữ)" },
            { value: "eve", label: "Eve (nữ, đa ngôn ngữ)" },
            { value: "clone đính kèm", label: "Clone từ file mẫu đính kèm" },
          ],
        },
        {
          id: "vidCaptionStyle",
          type: "select",
          label: "Kiểu phụ đề",
          def: "white",
          options: [
            { value: "white", label: "white - sạch" },
            { value: "paper", label: "paper - cắt giấy kem" },
            { value: "tắt", label: "Không burn-in phụ đề" },
          ],
        },
        {
          id: "vidMusicPrompt",
          type: "text",
          label: "Gợi ý nhạc BGM (Minimax)",
          def: "",
          ph: "vd: instrumental warm documentary, no vocals",
        },
        {
          group: "Nguồn & chất lượng",
          id: "vidPaperMode",
          type: "select",
          label: "Mode nguồn",
          def: "standard",
          options: [
            { value: "standard", label: "Standard (topic → poster)" },
            { value: "croll", label: "C-roll - neo ảnh chân dung/sản phẩm" },
            { value: "aroll", label: "A-roll - restyle talking-head" },
            { value: "local-engine", label: "Local engine - cắt element bay vào" },
          ],
        },
        {
          id: "vidImageRes",
          type: "select",
          label: "Độ phân giải ảnh keyframe",
          def: "1k",
          options: [
            { value: "1k", label: "1k (nhanh)" },
            { value: "2k", label: "2k" },
            { value: "4k", label: "4k (chậm/tốn)" },
          ],
        },
        {
          id: "vidApproveBeat",
          type: "select",
          label: "Duyệt beat map trước khi gen",
          def: "có",
          options: [
            { value: "có", label: "Có - dừng duyệt (tiết kiệm Atlas)" },
            { value: "không", label: "Bỏ duyệt (rủi ro tốn gen)" },
          ],
        },
      ],
    },
    {
      id: "remotion",
      pipeline: "remotion",
      label: "Đồ họa Remotion",
      blurb: "Data viz · UI · caption · maps",
      full: "Video đồ họa Remotion",
      when: "Biểu đồ, dashboard, chữ frame-perfect, maps, composition React.",
      example: "Tăng trưởng quý 3 → chart draw 30s + caption.",
      time: "Kéo tới 10 phút; chọn loại composition",
      topicPh: "Ví dụ: Số liệu tăng trưởng quý 3",
      needsUrl: false,
      assetsLabel: "Số liệu / ảnh / GeoJSON (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Link sheet, CSV, ảnh dashboard, GeoJSON…",
      caps: [
        "Data viz & UI motion",
        "Captions word-level",
        "Maps / geo flyover",
        "Studio + render ffmpeg",
        "Transparent / SaaS player",
      ],
      aspects: DEFAULT_ASPECTS,
      duration: {
        min: 10,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 30,
        hint: "15–40s thường đủ cho một beat số liệu. Tối đa 10 phút.",
      },
      slides: {
        min: 2,
        max: 20,
        step: 1,
        def: 4,
        label: "Số cảnh / sequence",
        hint: "Mỗi sequence một beat số liệu / UI / chữ.",
      },
      extras: [
        {
          group: "Loại composition",
          id: "vidRemotionKind",
          type: "select",
          label: "Trọng tâm",
          def: "data-viz",
          options: [
            { value: "data-viz", label: "Biểu đồ / số liệu" },
            { value: "ui-motion", label: "UI / product motion" },
            { value: "captions", label: "Caption / karaoke chữ" },
            { value: "maps", label: "Bản đồ / geo" },
            { value: "multi-scene", label: "Nhiều scene ghép" },
            { value: "mixed", label: "Hỗn hợp" },
          ],
        },
        {
          id: "vidFps",
          type: "select",
          label: "FPS",
          def: "30",
          options: [
            { value: "30", label: "30 fps (mặc định)" },
            { value: "24", label: "24 fps cinematic" },
            { value: "60", label: "60 fps mượt" },
          ],
        },
        {
          id: "vidChartStyle",
          type: "select",
          label: "Phong cách hình",
          def: "sạch",
          options: [
            { value: "sạch", label: "Sạch / corporate" },
            { value: "năng động", label: "Năng động / startup" },
            { value: "vui", label: "Vui / màu nổi" },
            { value: "theo brand tokens", label: "Bám brand tokens sản phẩm" },
          ],
        },
        {
          id: "vidDataAnim",
          type: "select",
          label: "Animation số / UI",
          def: "có",
          options: [
            { value: "có", label: "Có (count-up / chart draw)" },
            { value: "nhẹ", label: "Nhẹ" },
            { value: "không", label: "Tĩnh hơn" },
          ],
        },
        {
          group: "Xuất",
          id: "vidTransparent",
          type: "select",
          label: "Nền trong suốt",
          def: "không",
          options: [
            { value: "không", label: "Không (mp4 thường)" },
            { value: "có", label: "Có (WebM/ProRes transparent)" },
          ],
        },
        {
          id: "vidRemotionVoice",
          type: "select",
          label: "Lời đọc kèm",
          def: "không",
          options: [
            { value: "không", label: "Không lời" },
            { value: "có", label: "Có lời đọc" },
          ],
        },
        {
          id: "vidStudioPreview",
          type: "select",
          label: "Preview Remotion Studio",
          def: "có trước khi render",
          options: [
            { value: "có trước khi render", label: "Bật Studio rồi mới render" },
            { value: "render thẳng", label: "Render thẳng (nhanh)" },
          ],
        },
      ],
    },
    {
      id: "html-video",
      pipeline: "html-video",
      label: "HTML kinetic",
      blurb: "OmmiStudio · template + brand",
      full: "Video HTML → MP4 (OmmiStudio / nexu)",
      when: "Short marketing từ template HTML, brand pack, chữ kinetic (motion-anything).",
      example: "Brand pack quán cà phê → HTML kinetic 20s xuất mp4.",
      time: "Cần OmmiStudio (Node, Playwright, ffmpeg)",
      topicPh: "Ví dụ: Promo khai trương quán cà phê",
      needsUrl: false,
      assetsLabel: "Brand tokens / logo / màu (tuỳ chọn)",
      assetsHint: "Ghi hex màu, font, logo path nếu có.",
      assetsPh: "Logo, màu #…, font…",
      caps: [
        "html-video + Playwright",
        "motion-anything chữ kinetic",
        "html-still thumbnail",
        "Brand pack / template",
        "Ommi UI :5173",
      ],
      aspects: DEFAULT_ASPECTS,
      duration: {
        min: 8,
        max: MAX_DURATION_SEC,
        step: 1,
        def: 20,
        hint: "Short HTML thường 10–30s. Tối đa 10 phút.",
      },
      slides: {
        min: 1,
        max: 20,
        step: 1,
        def: 4,
        label: "Số scene HTML",
        hint: "Mỗi scene một layout HTML trước khi record.",
      },
      extras: [
        {
          group: "Template & brand",
          id: "vidHtmlTemplate",
          type: "select",
          label: "Kiểu template",
          def: "promo short",
          options: [
            { value: "promo short", label: "Promo short" },
            { value: "launch", label: "Launch / ra mắt" },
            { value: "feature list", label: "Danh sách tính năng" },
            { value: "testimonial", label: "Testimonial" },
            { value: "custom", label: "Tự mô tả trong kịch bản" },
          ],
        },
        {
          id: "vidKinetic",
          type: "select",
          label: "Chữ kinetic (motion-anything)",
          def: "có",
          options: [
            { value: "có", label: "Có chữ kinetic" },
            { value: "nhẹ", label: "Nhẹ" },
            { value: "không", label: "Không - layout tĩnh hơn" },
          ],
        },
        {
          id: "vidBrandTokens",
          type: "text",
          label: "Brand tokens (màu / font)",
          def: "",
          ph: "vd: primary #0B3D2E, accent #F4C95F, font Be Vietnam Pro",
        },
        {
          group: "Đầu ra phụ",
          id: "vidHtmlStill",
          type: "select",
          label: "Xuất thêm ảnh/PDF (html-still)",
          def: "thumbnail",
          options: [
            { value: "không", label: "Không" },
            { value: "thumbnail", label: "Thumbnail cover" },
            { value: "thumbnail+pdf", label: "Thumbnail + PDF poster" },
          ],
        },
        {
          id: "vidOmmiLocal",
          type: "select",
          label: "OmmiStudio local",
          def: "dùng nếu đang chạy",
          options: [
            { value: "dùng nếu đang chạy", label: "Dùng nếu :5173/:3001 sống" },
            { value: "chỉ hướng dẫn setup", label: "Chỉ đưa hướng dẫn cài" },
            { value: "manual pack", label: "Manual prompt-pack nếu thiếu máy" },
          ],
        },
      ],
    },
    {
      id: "auto",
      pipeline: "để đạo diễn chọn",
      label: "Javis chọn",
      blurb: "Đọc catalog rồi quyết",
      full: "Để Javis chọn pipeline phù hợp",
      when: "Chưa chắc kiểu nào - điền brief; đạo diễn chọn theo catalog lam-video.",
      example: "Giới thiệu quán cà phê → Javis chọn postcard / collage / HTML…",
      time: "Thời lượng + số cảnh gợi ý",
      topicPh: "Ví dụ: Video giới thiệu cửa hàng cà phê",
      needsUrl: false,
      assetsLabel: "Link / ảnh (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Có gì dán vào đây",
      caps: [
        "postcard / pixcel / paper / remotion / html",
        "Đổi pipeline nếu thiếu key",
        "Manual pack khi bí",
      ],
      aspects: DEFAULT_ASPECTS,
      duration: {
        min: 15,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 30,
        hint: "Gợi ý độ dài (tối đa 10 phút).",
      },
      slides: {
        min: 3,
        max: 30,
        step: 1,
        def: 5,
        label: "Số cảnh gợi ý",
        hint: "Gợi ý cho đạo diễn; có thể chỉnh theo pipeline được chọn.",
      },
      extras: [
        {
          group: "Ưu tiên chọn pipeline",
          id: "vidPriority",
          type: "select",
          label: "Ưu tiên",
          def: "cân bằng",
          options: [
            { value: "nhanh", label: "Làm nhanh (pixcel nếu được)" },
            { value: "đẹp cinematic", label: "Đẹp cinematic (postcard)" },
            { value: "collage giải thích", label: "Collage giải thích (paperdesign)" },
            { value: "data/UI", label: "Data / UI (Remotion)" },
            { value: "HTML brand", label: "HTML brand pack" },
            { value: "có lời", label: "Ưu tiên có lời đọc" },
            { value: "cân bằng", label: "Cân bằng" },
          ],
        },
        {
          id: "vidAvoidPipeline",
          type: "select",
          label: "Tránh pipeline",
          def: "không",
          options: [
            { value: "không", label: "Không tránh" },
            { value: "paperdesign", label: "Tránh paperdesign (thiếu Atlas)" },
            { value: "postcard-video", label: "Tránh postcard (thiếu Node)" },
            { value: "html-video", label: "Tránh Ommi/html-video" },
          ],
        },
        {
          id: "vidMustHave",
          type: "text",
          label: "Bắt buộc có trong video",
          def: "",
          ph: "Ví dụ: hiện logo, giá, CTA đăng ký…",
        },
      ],
    },
  ];

  var STEPS = [
    { id: "research", label: "Tìm hiểu", agents: ["nghien-cuu-chu-de-video"] },
    { id: "script", label: "Viết kịch bản", agents: ["bien-kich-video"] },
    { id: "direct", label: "Làm video", agents: ["dao-dien-video"] },
    { id: "qa", label: "Kiểm tra", agents: ["kiem-chung-video"] },
  ];

  var BASE_FIELD_IDS = [
    "vidTopic",
    "vidGoals",
    "vidAudience",
    "vidDuration",
    "vidSlides",
    "vidAspect",
    "vidLang",
    "vidChannel",
    "vidCta",
    "vidBrand",
    "vidTone",
    "vidAssets",
    "vidScript",
  ];

  function formatDuration(sec) {
    var n = Math.max(0, Math.round(Number(sec) || 0));
    if (n < 60) return n + " giây";
    var m = Math.floor(n / 60);
    var s = n % 60;
    if (s === 0) return m + " phút";
    return m + " phút " + s + " giây";
  }

  function durationBrief(sec) {
    var n = Math.max(0, Math.round(Number(sec) || 0));
    return formatDuration(n) + " (" + n + "s)";
  }

  function clamp(n, lo, hi) {
    n = Number(n);
    if (!isFinite(n)) n = lo;
    return Math.min(hi, Math.max(lo, n));
  }

  function brain() {
    try {
      if (typeof window.currentBrainPath === "function") return window.currentBrainPath() || "brain";
      return "brain";
    } catch (e) {
      return "brain";
    }
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function composeBrief(v) {
    var f = v.feat;
    var parts = [
      "Chủ đề: " + v.topic,
      "Mục tiêu: " + (v.goals || "(chưa ghi)"),
      "Audience: " + (v.audience || "(chưa ghi)"),
      "Độ dài: " + (v.durationLabel || durationBrief(v.durationSec || 30)),
      "Số slide / cảnh / shot: " + (v.slides || "(chưa ghi)"),
      "Tỉ lệ: " + (v.aspect || "9:16"),
      "Ngôn ngữ VO + chữ trên hình: " + (v.lang || "vi"),
      "Kênh: " + (v.channel || "(chưa ghi)"),
      "CTA: " + (v.cta || "(chưa ghi)"),
      "Cấm / brand: " + (v.brand || "(không)"),
      "Pipeline: " + (f.pipeline || "để đạo diễn chọn"),
      "Tone / vibe: " + (v.tone || "(chưa ghi)"),
    ];
    if (f.caps && f.caps.length) {
      parts.push("Năng lực pipeline cần tận dụng: " + f.caps.join("; "));
    }
    if (v.extras && v.extras.length) {
      parts.push("Yêu cầu theo kiểu «" + f.full + "»:");
      v.extras.forEach(function (ex) {
        parts.push("- " + ex.label + ": " + ex.value);
      });
    }
    if (v.assets) parts.push("Tài sản / URL: " + v.assets);
    if (v.script) parts.push("Kịch bản / beat dán sẵn:\n" + v.script);
    if (v.files && v.files.length) parts.push("File đính kèm:\n- " + v.files.join("\n- "));
    parts.push(
      "Yêu cầu UI Tạo video: làm đúng pipeline đã chọn; tôn trọng độ dài và số slide đã chọn; thiếu môi trường thì nói rõ và đưa Manual pack, không hứa suông."
    );
    return parts.join("\n");
  }

  function formatLogLine(raw) {
    var s = String(raw == null ? "" : raw);
    if (/^#{1,3}\s/.test(s.trim())) {
      return '<span class="jw-h">' + esc(s.trim().replace(/^#+\s*/, "")) + "</span>";
    }
    if (/^\[(step|status|step_start|xong bước|step_done)/i.test(s.trim())) {
      return '<span class="jw-step">' + esc(s) + "</span>";
    }
    return esc(s);
  }

  function agentToStep(agent) {
    var a = String(agent || "").toLowerCase();
    for (var i = 0; i < STEPS.length; i++) {
      for (var j = 0; j < STEPS[i].agents.length; j++) {
        if (a.indexOf(STEPS[i].agents[j]) >= 0) return i;
      }
    }
    return -1;
  }

  function capsHtml(f) {
    var caps = f.caps || [];
    if (!caps.length) return "";
    return (
      '<ul class="jw-feat-chips" aria-label="Năng lực tận dụng">' +
      caps
        .map(function (c) {
          return "<li>" + esc(c) + "</li>";
        })
        .join("") +
      "</ul>"
    );
  }

  function aspectsHtml(f, selected) {
    var opts = f.aspects && f.aspects.length ? f.aspects : DEFAULT_ASPECTS;
    var html = '<div class="jw-field"><label for="vidAspect">Khung hình *</label><select id="vidAspect">';
    opts.forEach(function (o, i) {
      var sel =
        (selected && selected === o.value) || (!selected && i === 0) ? " selected" : "";
      html +=
        '<option value="' +
        esc(o.value) +
        '"' +
        sel +
        ">" +
        esc(o.label) +
        "</option>";
    });
    html += "</select></div>";
    return html;
  }

  function extrasHtml(f) {
    var list = f.extras || [];
    if (!list.length) return "";
    var html =
      '<p class="jw-sec">3. Yêu cầu «' +
      esc(f.label) +
      '»</p><div class="jw-type-opts">';
    var lastGroup = "";
    list.forEach(function (ex) {
      if (ex.group && ex.group !== lastGroup) {
        html += '<p class="jw-subsec">' + esc(ex.group) + "</p>";
        lastGroup = ex.group;
      }
      html += '<div class="jw-field"><label for="' + esc(ex.id) + '">' + esc(ex.label) + "</label>";
      if (ex.type === "text") {
        html +=
          '<input id="' +
          esc(ex.id) +
          '" type="text" autocomplete="off" placeholder="' +
          esc(ex.ph || "") +
          '">';
      } else {
        html += '<select id="' + esc(ex.id) + '">';
        (ex.options || []).forEach(function (o) {
          html +=
            '<option value="' +
            esc(o.value) +
            '"' +
            (o.value === ex.def ? " selected" : "") +
            ">" +
            esc(o.label) +
            "</option>";
        });
        html += "</select>";
      }
      html += "</div>";
    });
    html += "</div>";
    return html;
  }

  function rangeField(opts) {
    return (
      '<div class="jw-field jw-field-range">' +
      '<div class="jw-range-head"><label for="' +
      esc(opts.id) +
      '">' +
      esc(opts.label) +
      '</label><span class="jw-range-val" id="' +
      esc(opts.valId) +
      '">' +
      esc(opts.valText) +
      "</span></div>" +
      '<input id="' +
      esc(opts.id) +
      '" type="range" min="' +
      opts.min +
      '" max="' +
      opts.max +
      '" step="' +
      opts.step +
      '" value="' +
      opts.value +
      '">' +
      '<div class="jw-range-ends"><span>' +
      esc(opts.minLabel) +
      "</span><span>" +
      esc(opts.maxLabel) +
      "</span></div>" +
      (opts.hint ? '<p class="jw-hint">' + esc(opts.hint) + "</p>" : "") +
      "</div>"
    );
  }

  window.renderTaoVideo = function (root) {
    if (!root) return;
    var uploaded = [];
    var es = null;
    var tabIdx = 0;
    var running = false;
    var stepIdx = -1;
    var draft = {};

    root.innerHTML =
      '<div class="jw jw-video" id="vidJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Tạo video</h2>" +
      '<p class="jw-lead">Chọn kiểu tab → kéo thời lượng/số cảnh → chỉnh yêu cầu theo pipeline → <b>Tạo video</b>.</p></div>' +
      "</div>" +
      '<div class="jw-tabs jw-tabs-video" role="tablist" id="vidTabs"></div>' +
      '<p class="jw-tab-hint" id="vidTabHint"></p>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="vidLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Đang làm gì</h3><div class="jw-status" id="vidStatus">Chưa chạy</div></div>' +
      '<ol class="jw-steps" id="vidSteps" aria-label="Các bước làm video"></ol>' +
      '<div class="jw-out" id="vidOut">' +
      '<div class="jw-empty" id="vidEmpty">' +
      "<strong>Bắt đầu từ bên trái</strong>" +
      "Chọn tab kiểu video, ghi chủ đề và mục tiêu, rồi bấm Tạo video. " +
      "Tiến trình hiện ở đây. File xong thường nằm trong Files → attachments/videos/." +
      "</div>" +
      '<pre class="jw-log" id="vidLog" hidden></pre>' +
      "</div></section></div></div>";

    var tabsEl = root.querySelector("#vidTabs");
    FEATURES.forEach(function (f, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "jw-tab jw-tab-stack" + (i === 0 ? " on" : "");
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", i === 0 ? "true" : "false");
      b.setAttribute("data-i", String(i));
      b.innerHTML =
        '<span class="jw-tab-label">' +
        esc(f.label) +
        '</span><span class="jw-tab-blurb">' +
        esc(f.blurb) +
        "</span>";
      tabsEl.appendChild(b);
    });

    function feat() {
      return FEATURES[tabIdx] || FEATURES[0];
    }

    function fieldIds() {
      var ids = BASE_FIELD_IDS.slice();
      (feat().extras || []).forEach(function (ex) {
        ids.push(ex.id);
      });
      return ids;
    }

    function paintTabHint() {
      var f = feat();
      var el = root.querySelector("#vidTabHint");
      if (!el) return;
      el.innerHTML =
        "<b>" +
        esc(f.full) +
        "</b> · " +
        esc(f.blurb) +
        ' <span class="dim">· ' +
        esc(f.time) +
        "</span>";
    }

    function paintSteps() {
      var el = root.querySelector("#vidSteps");
      if (!el) return;
      el.innerHTML = STEPS.map(function (s, i) {
        var cls = "jw-step-item" + (i === stepIdx ? " on" : i < stepIdx ? " done" : "");
        return (
          '<li class="' +
          cls +
          '"><span class="n">' +
          (i + 1) +
          '</span><span class="jw-step-lab">' +
          esc(s.label) +
          "</span></li>"
        );
      }).join("");
    }

    function setStatus(msg, kind) {
      var el = root.querySelector("#vidStatus");
      if (!el) return;
      el.textContent = msg || "";
      el.className = "jw-status" + (kind === false ? " err" : kind === true ? " ok" : "");
    }

    function showLog() {
      var empty = root.querySelector("#vidEmpty");
      var log = root.querySelector("#vidLog");
      if (empty) empty.hidden = true;
      if (log) log.hidden = false;
    }

    function appendLog(line) {
      showLog();
      var log = root.querySelector("#vidLog");
      if (!log) return;
      log.innerHTML += formatLogLine(line) + "\n";
      var out = root.querySelector("#vidOut");
      if (out) out.scrollTop = out.scrollHeight;
    }

    function advanceStep(agent) {
      var i = agentToStep(agent);
      if (i >= 0 && i !== stepIdx) {
        stepIdx = i;
        paintSteps();
      }
    }

    function saveDraft() {
      fieldIds().forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el) draft[id] = el.value;
      });
    }

    function restoreDraft() {
      var f = feat();
      var dCfg = f.duration || {};
      var sCfg = f.slides || {};
      var durEl = root.querySelector("#vidDuration");
      var slidesEl = root.querySelector("#vidSlides");

      BASE_FIELD_IDS.forEach(function (id) {
        if (id === "vidDuration" || id === "vidSlides") return;
        var el = root.querySelector("#" + id);
        if (!el || draft[id] == null) return;
        if (id === "vidAspect") {
          var ok = false;
          for (var oi = 0; oi < el.options.length; oi++) {
            if (el.options[oi].value === draft[id]) {
              ok = true;
              break;
            }
          }
          if (ok) el.value = draft[id];
          return;
        }
        el.value = draft[id];
      });

      if (durEl) {
        var rawDur = draft.vidDuration != null ? draft.vidDuration : dCfg.def;
        durEl.value = String(clamp(rawDur, dCfg.min || 10, dCfg.max || MAX_DURATION_SEC));
      }
      if (slidesEl) {
        var rawSl = draft.vidSlides != null ? draft.vidSlides : sCfg.def;
        slidesEl.value = String(clamp(rawSl, sCfg.min || 1, sCfg.max || 24));
      }

      (f.extras || []).forEach(function (ex) {
        var el = root.querySelector("#" + ex.id);
        if (!el) return;
        if (draft[ex.id] != null && draft[ex.id] !== "") {
          el.value = draft[ex.id];
        } else if (ex.def != null && ex.type !== "text") {
          el.value = ex.def;
        } else if (ex.type === "text" && ex.def) {
          el.value = ex.def;
        }
      });

      syncRangeLabels();
    }

    function syncRangeLabels() {
      var f = feat();
      var durEl = root.querySelector("#vidDuration");
      var durVal = root.querySelector("#vidDurationVal");
      if (durEl && durVal) {
        durVal.textContent = formatDuration(durEl.value);
      }
      var slidesEl = root.querySelector("#vidSlides");
      var slidesVal = root.querySelector("#vidSlidesVal");
      if (slidesEl && slidesVal) {
        var n = slidesEl.value;
        var lab = (f.slides && f.slides.label) || "Số cảnh";
        slidesVal.textContent = n + " · " + lab.replace(/^Số\s+/i, "").toLowerCase();
      }
    }

    function paintLeft() {
      var f = feat();
      var d = f.duration || { min: 10, max: MAX_DURATION_SEC, step: 5, def: 30 };
      var s = f.slides || { min: 3, max: 24, step: 1, def: 5, label: "Số cảnh" };
      var left = root.querySelector("#vidLeft");
      left.innerHTML =
        '<div class="jw-brief jw-brief-lite">' +
        '<p class="jw-brief-kicker">Kiểu đang chọn</p>' +
        "<h3>" +
        esc(f.full) +
        "</h3>" +
        "<p>" +
        esc(f.when) +
        "</p>" +
        '<p class="jw-ex">Ví dụ: ' +
        esc(f.example) +
        "</p>" +
        capsHtml(f) +
        "</div>" +
        '<p class="jw-sec">1. Bạn muốn nói gì</p>' +
        '<div class="jw-field"><label for="vidTopic">Chủ đề *</label>' +
        '<input id="vidTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        '<div class="jw-field"><label for="vidGoals">Mục tiêu *</label>' +
        '<textarea id="vidGoals" rows="2" placeholder="Ví dụ: Để mọi người nhớ sản phẩm / muốn thử / hiểu một ý"></textarea></div>' +
        '<div class="jw-field"><label for="vidAudience">Người xem</label>' +
        '<input id="vidAudience" type="text" placeholder="Ví dụ: Phụ huynh, chủ quán, học sinh"></div>' +
        '<p class="jw-sec">2. Hình thức</p>' +
        rangeField({
          id: "vidDuration",
          valId: "vidDurationVal",
          label: "Dài bao lâu *",
          min: d.min,
          max: d.max,
          step: d.step || 5,
          value: d.def,
          valText: formatDuration(d.def),
          minLabel: formatDuration(d.min),
          maxLabel: formatDuration(d.max),
          hint: d.hint || "",
        }) +
        rangeField({
          id: "vidSlides",
          valId: "vidSlidesVal",
          label: (s.label || "Số slide / cảnh") + " *",
          min: s.min,
          max: s.max,
          step: s.step || 1,
          value: s.def,
          valText: String(s.def),
          minLabel: String(s.min),
          maxLabel: String(s.max),
          hint: s.hint || "",
        }) +
        '<div class="jw-row2">' +
        aspectsHtml(f, draft.vidAspect) +
        '<div class="jw-field"><label for="vidLang">Ngôn ngữ *</label>' +
        '<select id="vidLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div></div>' +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="vidChannel">Đăng ở đâu</label>' +
        '<input id="vidChannel" type="text" placeholder="Reels, TikTok, YouTube, Ads…"></div>' +
        '<div class="jw-field"><label for="vidCta">CTA / lời kêu gọi</label>' +
        '<input id="vidCta" type="text" placeholder="Ví dụ: Tải app, Đăng ký, Inbox…"></div></div>' +
        '<div class="jw-field"><label for="vidBrand">Cấm / brand / lưu ý</label>' +
        '<input id="vidBrand" type="text" placeholder="Màu cấm, không dùng đối thủ, logo phải hiện…"></div>' +
        '<div class="jw-field"><label for="vidAssets">' +
        esc(f.assetsLabel) +
        "</label>" +
        '<textarea id="vidAssets" rows="2" placeholder="' +
        esc(f.assetsPh) +
        '"></textarea>' +
        (f.assetsHint ? '<p class="jw-hint">' + esc(f.assetsHint) + "</p>" : "") +
        "</div>" +
        extrasHtml(f) +
        '<details class="jw-more">' +
        "<summary>Thêm kịch bản, tone, file (tuỳ chọn)</summary>" +
        '<div class="jw-field"><label for="vidTone">Giọng / cảm xúc</label>' +
        '<input id="vidTone" type="text" placeholder="Ví dụ: Ấm áp, sạch sẽ, vui, chuyên nghiệp"></div>' +
        '<div class="jw-field"><label for="vidScript">Kịch bản sẵn có</label>' +
        '<textarea id="vidScript" rows="5" placeholder="Có outline hoặc lời thoại thì dán vào. Để trống = Javis viết giúp."></textarea></div>' +
        '<div class="jw-field"><label for="vidFiles">Đính kèm ảnh / logo / file nghe</label>' +
        '<input id="vidFiles" type="file" multiple>' +
        '<p class="jw-hint" id="vidFileList">Chưa chọn file</p></div>' +
        '<div class="jw-actions jw-actions-ghost">' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="vidSeed">Cài bộ làm video (một lần)</button>' +
        "</div></details>" +
        '<div class="jw-actions jw-actions-main">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="vidRun">Tạo video · ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="vidStop" disabled>Dừng xem</button>' +
        "</div>" +
        '<p class="jw-hint jw-hint-foot">Lần đầu có thể bấm «Cài bộ làm video» trong mục tuỳ chọn. Các lần sau cứ Tạo video.</p>';

      restoreDraft();
      wireLeft();
      paintTabHint();
    }

    function wireLeft() {
      fieldIds().forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (!el) return;
        el.addEventListener("change", saveDraft);
        el.addEventListener("input", function () {
          if (id === "vidDuration" || id === "vidSlides") syncRangeLabels();
          saveDraft();
        });
      });

      var filesEl = root.querySelector("#vidFiles");
      if (filesEl) {
        filesEl.onchange = async function () {
          var files = Array.from(filesEl.files || []);
          uploaded = [];
          var list = root.querySelector("#vidFileList");
          if (!files.length) {
            if (list) list.textContent = "Chưa chọn file";
            return;
          }
          if (list) list.textContent = "Đang tải…";
          for (var i = 0; i < files.length; i++) {
            var fd = new FormData();
            fd.append("file", files[i]);
            fd.append("brain", brain());
            try {
              var r = await (await fetch("/upload", { method: "POST", body: fd })).json();
              if (r && (r.path || r.name)) uploaded.push(r.path || r.name);
              else if (r && r.error) appendLog("Upload lỗi: " + r.error);
            } catch (e) {
              appendLog("Upload lỗi: " + ((e && e.message) || e));
            }
          }
          if (list) {
            list.textContent = uploaded.length
              ? "Đã tải: " + uploaded.join(", ")
              : "Không tải được file.";
          }
        };
      }

      var stopBtn = root.querySelector("#vidStop");
      if (stopBtn) {
        stopBtn.onclick = function () {
          try {
            if (es) es.close();
          } catch (e) {}
          es = null;
          setBusy(false, "Đã dừng theo dõi (việc trên máy có thể vẫn chạy).", true);
        };
      }

      var runBtn = root.querySelector("#vidRun");
      if (runBtn) runBtn.onclick = run;

      var seedBtn = root.querySelector("#vidSeed");
      if (seedBtn) {
        seedBtn.onclick = async function () {
          if (running) return;
          seedBtn.disabled = true;
          seedBtn.textContent = "Đang cài…";
          setStatus("Đang cài bộ làm video…");
          try {
            var fd = new FormData();
            fd.append("brain", brain());
            var r = await (await fetch("/studio/seed-video", { method: "POST", body: fd })).json();
            if (!r || !r.ok) {
              setStatus((r && r.error) || "Cài chưa xong", false);
              return;
            }
            setStatus("Đã sẵn sàng. Bạn có thể bấm Tạo video.", true);
          } catch (e) {
            setStatus(String((e && e.message) || e), false);
          } finally {
            seedBtn.disabled = false;
            seedBtn.textContent = "Cài bộ làm video (một lần)";
          }
        };
      }
    }

    function selectTab(i) {
      saveDraft();
      tabIdx = i;
      tabsEl.querySelectorAll(".jw-tab").forEach(function (btn, j) {
        var on = j === i;
        btn.classList.toggle("on", on);
        btn.setAttribute("aria-selected", on ? "true" : "false");
      });
      paintLeft();
    }

    function clearFieldErrors() {
      root.querySelectorAll(".jw-field.err").forEach(function (w) {
        w.classList.remove("err");
      });
    }

    function markField(id, bad) {
      var el = root.querySelector("#" + id);
      if (!el) return;
      var wrap = el.closest(".jw-field");
      if (wrap) wrap.classList.toggle("err", !!bad);
      if (bad) {
        try {
          el.focus();
        } catch (e) {}
      }
    }

    function setBusy(busy, statusMsg, statusOk) {
      running = !!busy;
      var f = feat();
      var runBtn = root.querySelector("#vidRun");
      var stopBtn = root.querySelector("#vidStop");
      var seedBtn = root.querySelector("#vidSeed");
      if (runBtn) {
        runBtn.disabled = busy;
        runBtn.classList.toggle("jw-busy", busy);
        runBtn.textContent = busy ? "Đang tạo…" : "Tạo video · " + f.label;
      }
      if (stopBtn) stopBtn.disabled = !busy;
      if (seedBtn) seedBtn.disabled = busy;
      tabsEl.querySelectorAll(".jw-tab").forEach(function (t) {
        t.disabled = busy;
      });
      if (statusMsg != null) setStatus(statusMsg, statusOk);
    }

    function readExtras() {
      var f = feat();
      var out = [];
      (f.extras || []).forEach(function (ex) {
        var el = root.querySelector("#" + ex.id);
        var val = el ? String(el.value || "").trim() : "";
        if (!val && ex.type === "text") return;
        if (!val) val = ex.def || "";
        out.push({ id: ex.id, label: ex.label, value: val });
      });
      return out;
    }

    function validateInputs() {
      clearFieldErrors();
      var f = feat();
      saveDraft();
      var topic = ((root.querySelector("#vidTopic") || {}).value || "").trim();
      var goals = ((root.querySelector("#vidGoals") || {}).value || "").trim();
      var assets = ((root.querySelector("#vidAssets") || {}).value || "").trim();
      var durCfg = f.duration || {};
      var slCfg = f.slides || {};
      var durationSec = clamp(
        (root.querySelector("#vidDuration") || {}).value,
        durCfg.min || 10,
        durCfg.max || MAX_DURATION_SEC
      );
      var slides = clamp(
        (root.querySelector("#vidSlides") || {}).value,
        slCfg.min || 1,
        slCfg.max || 40
      );
      var missing = [];
      if (!topic) {
        markField("vidTopic", true);
        missing.push("Chủ đề");
      }
      if (!goals) {
        markField("vidGoals", true);
        missing.push("Mục tiêu");
      }
      if (f.needsUrl && !assets) {
        markField("vidAssets", true);
        missing.push("Link / ảnh sản phẩm");
      }
      if (missing.length) {
        setStatus("Thiếu: " + missing.join(", ") + ". Điền bên trái rồi bấm Tạo video.", false);
        return null;
      }
      return {
        topic: topic,
        goals: goals,
        audience: ((root.querySelector("#vidAudience") || {}).value || "").trim(),
        durationSec: durationSec,
        durationLabel: durationBrief(durationSec),
        slides: slides,
        aspect: ((root.querySelector("#vidAspect") || {}).value || "9:16").trim(),
        lang: ((root.querySelector("#vidLang") || {}).value || "vi").trim(),
        channel: ((root.querySelector("#vidChannel") || {}).value || "").trim(),
        cta: ((root.querySelector("#vidCta") || {}).value || "").trim(),
        brand: ((root.querySelector("#vidBrand") || {}).value || "").trim(),
        tone: ((root.querySelector("#vidTone") || {}).value || "").trim(),
        assets: assets,
        script: ((root.querySelector("#vidScript") || {}).value || "").trim(),
        extras: readExtras(),
        files: uploaded.slice(),
        feat: f,
      };
    }

    function finishBusy(statusMsg, statusOk) {
      try {
        if (es) es.close();
      } catch (e) {}
      es = null;
      if (statusOk) {
        stepIdx = STEPS.length - 1;
        paintSteps();
      }
      setBusy(false, statusMsg, statusOk);
    }

    tabsEl.querySelectorAll(".jw-tab").forEach(function (btn) {
      btn.onclick = function () {
        if (running) {
          setStatus("Đang chạy - chờ xong hoặc bấm Dừng xem trước khi đổi tab.", false);
          return;
        }
        selectTab(parseInt(btn.getAttribute("data-i"), 10) || 0);
      };
    });

    async function run() {
      if (running) return;
      var v = validateInputs();
      if (!v) return;

      var f = v.feat;
      var brief = composeBrief(v);

      stepIdx = 0;
      paintSteps();
      setBusy(true, "Đang tạo «" + f.full + "»…");
      if (es) {
        try {
          es.close();
        } catch (e1) {}
        es = null;
      }
      var log = root.querySelector("#vidLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-video", { method: "POST", body: fd0 });
      } catch (e0) {}

      var url =
        "/workflows/run?slug=" +
        encodeURIComponent("bo-video-da-pipeline") +
        "&brain=" +
        encodeURIComponent(brain()) +
        "&input=" +
        encodeURIComponent(brief);
      es = new EventSource(url);
      es.onmessage = function (ev) {
        try {
          var data = JSON.parse(ev.data);
          var typ = data.type || "";
          if (typ === "token" || typ === "text" || typ === "chunk") {
            appendLog(data.text || data.token || data.content || "");
          } else if (typ === "step" || typ === "status" || typ === "step_start") {
            advanceStep(data.agent || data.message || "");
            appendLog(
              "[" + typ + "] " + (data.message || data.agent || data.step || JSON.stringify(data))
            );
          } else if (typ === "step_done") {
            advanceStep(data.agent || "");
            appendLog("[xong bước] " + (data.agent || ""));
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 5000 ? out.slice(0, 5000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            finishBusy("Lỗi khi tạo video", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 8000 ? res.slice(0, 8000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            finishBusy("Xong. Xem Files → attachments/videos/ (hoặc đường dẫn trong log).", true);
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        finishBusy("Mất kết nối (có thể đã xong hoặc lỗi). Xem log bên dưới.", false);
      };
    }

    paintSteps();
    paintLeft();
  };
})();
