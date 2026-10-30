/* SA Embroidery Chat Widget — with product slideshow & cart */

(() => {
  'use strict';

  const cfg = Object.assign({
    api: (['localhost', '127.0.0.1'].includes(location.hostname) && location.port !== '8000' ? 'http://localhost:8000/chat' : '/chat'),
    productsApi: 'https://sa-embroidery-backend.onrender.com/api/read/Products',
    site: 'https://saembroidery.com',
    whatsapp: '923167937030',
    brand: 'SA Embroidery'
  }, window.SA_CHAT_CONFIG || {});

  /* ─── STYLES ─────────────────────────────────────────────────────────── */
  /* ─── STYLES (Matching saembroidery.com: Crisp Black, Charcoal, Slate Gray & Clean White) ─── */
  const css = `
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

  #sa-panel,#sa-launcher,#sa-slide-panel{font-family:'Plus Jakarta Sans',system-ui,-apple-system,sans-serif}
  #sa-panel *,#sa-slide-panel *{box-sizing:border-box}

  /* Launcher - Sleek Dark Charcoal Black */
  #sa-launcher{
    position:fixed;right:25px;bottom:25px;z-index:99999;
    width:62px;height:62px;
    border:1px solid rgba(255,255,255,.18);
    border-radius:20px;
    display:grid;place-items:center;
    color:#fff;
    background:linear-gradient(135deg,#09090b 0%,#18181b 60%,#27272a 100%);
    box-shadow:0 12px 35px rgba(0,0,0,.35),0 2px 8px rgba(0,0,0,.15);
    cursor:pointer;
    transition:transform .2s ease,box-shadow .2s ease,opacity .2s ease;
  }
  #sa-launcher:hover{transform:translateY(-3px);box-shadow:0 18px 45px rgba(0,0,0,.45)}
  #sa-launcher:focus-visible,#sa-panel button:focus-visible,#sa-panel input:focus-visible,#sa-panel a:focus-visible,#sa-slide-panel button:focus-visible{outline:3px solid #18181b;outline-offset:2px}

  /* Chat panel - Fresh, high-contrast crisp white & modern slate */
  #sa-panel{
    --sa-ink:#0f172a;
    --sa-charcoal:#18181b;
    --sa-slate:#334155;
    --sa-line:#e2e8f0;
    --sa-muted:#64748b;
    --sa-accent:#2563eb;
    position:fixed;z-index:99998;right:24px;bottom:106px;
    width:min(428px,calc(100vw - 28px));height:min(700px,calc(100dvh - 124px));
    display:none;flex-direction:column;
    background:#ffffff;color:var(--sa-ink);
    border:1px solid #e2e8f0;border-radius:22px;overflow:hidden;
    box-shadow:0 25px 70px rgba(0,0,0,.22),0 4px 18px rgba(0,0,0,.08);
  }
  #sa-panel.open{display:flex;animation:sa-enter .22s ease both}
  @keyframes sa-enter{from{opacity:0;transform:translateY(10px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)}}

  /* ── LEFT SLIDE PANEL ───────────────────────────────────────────────── */
  #sa-slide-panel{
    position:fixed;z-index:99997;
    bottom:106px;
    right:calc(24px + min(428px,calc(100vw - 28px)) + 10px);
    width:270px;height:290px;
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:18px;
    overflow:hidden;
    box-shadow:0 12px 40px rgba(0,0,0,.18),0 2px 8px rgba(0,0,0,.06);
    display:none;flex-direction:column;
    transform:translateX(14px);opacity:0;
    transition:transform .32s cubic-bezier(.22,1,.36,1),opacity .28s ease;
  }
  #sa-slide-panel.sa-slide-open{display:flex}
  #sa-slide-panel.sa-slide-visible{transform:translateX(0);opacity:1}

  /* Slide panel header - Modern Charcoal */
  .sa-sp-head{
    background:linear-gradient(135deg,#09090b 0%,#18181b 70%,#27272a 100%);
    color:#fff;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;
    position:relative;
  }
  .sa-sp-head:after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:rgba(255,255,255,.15)}
  .sa-sp-title{font-size:11px;font-weight:700;letter-spacing:-.1px}
  .sa-sp-close{border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.09);color:#fff;width:22px;height:22px;border-radius:6px;font-size:15px;line-height:1;cursor:pointer;transition:background .2s;display:grid;place-items:center}
  .sa-sp-close:hover{background:rgba(255,255,255,.22)}

  /* Product tabs in slide panel */
  .sa-sp-tabs{display:flex;gap:4px;padding:6px 8px;border-bottom:1px solid #f1f5f9;background:#f8fafc;overflow-x:auto;scrollbar-width:none;flex-shrink:0}
  .sa-sp-tabs::-webkit-scrollbar{display:none}
  .sa-sp-tab{background:#ffffff;border:1px solid #e2e8f0;border-radius:6px;padding:4px 7px;font-size:9px;font-weight:700;color:#334155;cursor:pointer;white-space:nowrap;transition:all .15s;flex-shrink:0}
  .sa-sp-tab.active{background:#09090b;color:#fff;border-color:#09090b}
  .sa-sp-tab:hover:not(.active){background:#f1f5f9}

  /* Slideshow area */
  .sa-sp-slides{flex:1;min-height:0;position:relative;overflow:hidden;background:#f8fafc}
  .sa-sp-slide{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:10px;opacity:0;transform:translateX(30px);transition:opacity .3s ease,transform .3s ease;pointer-events:none}
  .sa-sp-slide.active{opacity:1;transform:translateX(0);pointer-events:auto}
  .sa-sp-slide.exit{opacity:0;transform:translateX(-30px)}
  .sa-sp-slide img{max-width:100%;max-height:100%;object-fit:contain;border-radius:10px;background:#fff;border:1px solid #e2e8f0;box-shadow:0 4px 14px rgba(0,0,0,.06)}

  /* Slide dots */
  .sa-sp-dots{display:flex;gap:4px;justify-content:center;padding:5px 8px;flex-shrink:0;flex-wrap:wrap;background:#fff}
  .sa-sp-dot{width:5px;height:5px;border-radius:50%;background:#cbd5e1;border:none;cursor:pointer;padding:0;transition:background .2s,transform .2s}
  .sa-sp-dot.active{background:#09090b;transform:scale(1.4)}

  /* Slide nav arrows */
  .sa-sp-nav{position:absolute;top:50%;transform:translateY(-50%);background:rgba(255,255,255,.94);border:1px solid #cbd5e1;color:#0f172a;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;cursor:pointer;font-size:12px;z-index:2;transition:all .15s;box-shadow:0 1px 5px rgba(0,0,0,.1)}
  .sa-sp-nav:hover{background:#fff;box-shadow:0 3px 10px rgba(0,0,0,.15)}
  .sa-sp-prev{left:6px}
  .sa-sp-next{right:6px}

  /* Product info in slide panel */
  .sa-sp-info{padding:8px 10px;border-top:1px solid #e2e8f0;background:#fff;flex-shrink:0}
  .sa-sp-name{font-size:10.5px;font-weight:750;color:#0f172a;line-height:1.35;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .sa-sp-meta{display:none}
  .sa-sp-price{display:inline-block;font-size:11.5px;font-weight:800;color:#0f172a;margin-bottom:7px}

  /* Cart button - Matching website Get Bulk Pricing / Request Quote */
  .sa-cart-btn{
    width:100%;padding:8px 10px;
    background:#18181b;
    color:#fff;border:none;border-radius:8px;
    font-size:10.5px;font-weight:700;
    cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;
    transition:all .2s;letter-spacing:.1px;
    box-shadow:0 2px 8px rgba(0,0,0,.16);
  }
  .sa-cart-btn:hover{background:#27272a;transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.22)}
  .sa-cart-btn:active{transform:translateY(0)}
  .sa-cart-btn svg{flex-shrink:0;width:12px;height:12px}

  /* WA button in slide panel - Crisp WhatsApp Green */
  .sa-sp-wa{
    margin:0 10px 8px;padding:6px 10px;
    background:#25D366;border:none;
    color:#ffffff;border-radius:8px;
    font-size:9.5px;font-weight:700;
    display:flex;align-items:center;justify-content:center;gap:5px;
    text-decoration:none;cursor:pointer;transition:all .15s;
    box-shadow:0 2px 6px rgba(37,211,102,.25);
  }
  .sa-sp-wa:hover{background:#20ba59;transform:translateY(-1px)}
  .sa-sp-wa svg{width:11px;height:11px;flex-shrink:0}

  /* ── CHAT PANEL INTERNAL ─────────────────────────────────────────────── */
  /* Header - Premium Black/Charcoal matching website top bar */
  .sa-head{
    background:linear-gradient(135deg,#09090b 0%,#18181b 60%,#27272a 100%);
    color:#fff;padding:18px 18px 16px;
    display:flex;align-items:center;gap:12px;position:relative;flex-shrink:0;
  }
  .sa-head:after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:rgba(255,255,255,.12)}
  .sa-avatar{width:42px;height:42px;display:grid;place-items:center;border-radius:12px;background:#27272a;border:1px solid rgba(255,255,255,.2);font-weight:800;font-size:14px;letter-spacing:-.3px;color:#fff;flex:none}
  .sa-head-meta{flex:1;min-width:0}
  .sa-head-meta b{display:block;font-size:14.5px;font-weight:750;letter-spacing:-.3px;line-height:1.35;color:#ffffff}
  .sa-head-meta small{display:block;font-size:11px;color:#a1a1aa;line-height:1.5;margin-top:2px}
  .sa-availability{display:inline-flex;align-items:center;gap:5px;font-size:10px;color:#d4d4d8;margin-top:4px}
  .sa-availability:before{content:'';width:6px;height:6px;background:#22c55e;border-radius:50%;box-shadow:0 0 0 3px rgba(34,197,94,.25)}
  .sa-x{border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.08);color:#fff;width:28px;height:28px;border-radius:8px;font-size:20px;line-height:1;cursor:pointer;transition:background .2s}
  .sa-x:hover{background:rgba(255,255,255,.2)}

  /* Action Chips - Matching saembroidery.com pills */
  .sa-actions{padding:10px 14px;display:flex;gap:7px;overflow-x:auto;flex-wrap:nowrap;scrollbar-width:none;border-bottom:1px solid #f1f5f9;background:#ffffff;flex-shrink:0}
  .sa-actions::-webkit-scrollbar{display:none}
  .sa-chip{
    background:#f8fafc;border:1px solid #e2e8f0;border-radius:9999px;
    padding:7px 12px;font-size:10.5px;white-space:nowrap;cursor:pointer;
    color:#1e293b;font-weight:650;transition:all .2s;
  }
  .sa-chip:hover{background:#09090b;border-color:#09090b;color:#ffffff}

  /* Chat Messages Container - Fresh Off-White / Crisp Neutral */
  .sa-messages{
    flex:1;min-height:0;overflow:auto;
    background:#f8fafc;
    padding:16px 14px;display:flex;flex-direction:column;gap:12px;
    scrollbar-width:thin;scrollbar-color:#cbd5e1 transparent;
  }

  /* Chat Bubbles */
  .sa-bubble{max-width:88%;padding:11px 14px;border-radius:14px;font-size:12.6px;line-height:1.68;white-space:pre-wrap;overflow-wrap:anywhere;letter-spacing:.01px}
  .sa-bot{align-self:flex-start;background:#ffffff;border:1px solid #e2e8f0;color:#0f172a;border-top-left-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,.04)}
  .sa-bubble strong{font-weight:750;color:#09090b}.sa-bubble em{font-style:italic}
  .sa-bubble a.sa-link{color:#2563eb;font-weight:700;text-decoration:underline;word-break:break-all;transition:color .15s}
  .sa-bubble a.sa-link:hover{color:#1d4ed8}
  .sa-action-btn{display:inline-flex;align-items:center;gap:6px;margin-top:8px;padding:8px 13px;background:#18181b;color:#fff!important;text-decoration:none!important;border-radius:8px;font-size:11.5px;font-weight:700;box-shadow:0 2px 8px rgba(0,0,0,.15);transition:background .2s}
  .sa-action-btn:hover{background:#27272a}
  .sa-user{align-self:flex-end;background:#18181b;color:#ffffff;border-top-right-radius:4px;box-shadow:0 3px 10px rgba(0,0,0,.15)}

  /* Welcome Banner - Clean Corporate */
  .sa-welcome{
    align-self:stretch;border:1px solid #e2e8f0;border-radius:14px;
    padding:16px 16px;background:linear-gradient(135deg,#ffffff 60%,#f8fafc);
    box-shadow:0 4px 16px rgba(0,0,0,.04);display:flex;flex-direction:column;gap:6px;
  }
  .sa-welcome-kicker{font-size:9.5px;letter-spacing:1.2px;font-weight:800;color:#71717a;text-transform:uppercase}
  .sa-welcome-title{font-size:18px;line-height:1.3;font-weight:800;color:#09090b;letter-spacing:-.4px}
  .sa-welcome-desc{font-size:12px;line-height:1.6;color:#475569}
  .sa-welcome-rule{width:32px;height:2px;background:#18181b;border-radius:2px;margin:2px 0}

  /* Product cards in chat - Matching saembroidery.com cards */
  .sa-products{width:100%;display:grid;gap:8px}
  .sa-product{
    background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;
    display:flex;gap:10px;padding:10px;text-decoration:none;color:#0f172a;
    transition:transform .15s,box-shadow .15s;align-items:center;
    box-shadow:0 1px 4px rgba(0,0,0,.03);
  }
  .sa-product:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.08);border-color:#cbd5e1}
  .sa-product-thumb{width:52px;height:52px;object-fit:contain;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;flex-shrink:0}
  .sa-product-thumb-placeholder{width:52px;height:52px;background:#f1f5f9;border-radius:8px;border:1px solid #e2e8f0;display:grid;place-items:center;font-size:18px;flex-shrink:0}
  .sa-product-content{min-width:0;flex:1}
  .sa-product strong{font-size:11.8px;line-height:1.35;display:block;margin-bottom:2px;color:#0f172a}
  .sa-product small{display:block;font-size:10px;color:#64748b;line-height:1.45}
  .sa-product em{display:inline-block;font-size:11px;font-style:normal;color:#0f172a;margin-top:4px;font-weight:800}
  .sa-product-actions{display:flex;flex-direction:column;gap:5px;flex-shrink:0}
  .sa-view-btn{background:#f8fafc;border:1px solid #e2e8f0;color:#0f172a;border-radius:6px;padding:5px 8px;font-size:9.5px;font-weight:700;cursor:pointer;transition:all .15s;white-space:nowrap}
  .sa-view-btn:hover{background:#e2e8f0}
  .sa-mini-cart{
    background:#18181b;color:#fff;border:none;border-radius:6px;
    padding:5px 8px;font-size:9.5px;font-weight:700;
    cursor:pointer;transition:all .15s;display:flex;align-items:center;gap:4px;white-space:nowrap;
  }
  .sa-mini-cart:hover{background:#27272a;transform:translateY(-1px)}

  /* Compose Input Area - Crisp White with Charcoal Send Button */
  .sa-compose{padding:12px 14px 8px;border-top:1px solid #f1f5f9;display:flex;gap:8px;background:#ffffff;flex-shrink:0}
  .sa-compose input{
    flex:1;min-width:0;background:#ffffff;border:1px solid #cbd5e1;
    border-radius:10px;padding:11px 12px;font-size:12px;min-height:44px;
    color:#0f172a;outline:none;transition:border-color .2s,box-shadow .2s;
  }
  .sa-compose input:focus{border-color:#18181b;box-shadow:0 0 0 3px rgba(24,24,27,.08)}
  .sa-compose button{
    border:0;border-radius:10px;background:#18181b;color:white;
    min-width:44px;cursor:pointer;font-size:16px;transition:background .2s;
  }
  .sa-compose button:hover{background:#27272a}
  .sa-compose button:disabled{opacity:.5;cursor:wait}

  /* Footer & WhatsApp CTA */
  .sa-foot{padding:0 14px 12px;color:#64748b;background:#ffffff;text-align:center;font-size:9.5px}
  .sa-foot a{color:#0f172a;text-decoration:none;font-weight:750}
  .sa-foot a:hover{text-decoration:underline}
  .sa-quote-link{
    align-self:flex-start;background:#25D366;border:none;
    color:#ffffff;text-decoration:none;padding:8px 12px;
    border-radius:8px;font-size:11px;font-weight:750;
    box-shadow:0 2px 8px rgba(37,211,102,.25);transition:background .15s;
  }
  .sa-quote-link:hover{background:#20ba59}

  @media(max-width:800px){
    #sa-slide-panel{display:none !important}
    #sa-panel{right:8px;bottom:80px;width:calc(100vw - 16px);height:min(720px,calc(100dvh - 95px));border-radius:18px}
    #sa-launcher{bottom:14px;right:14px;width:56px;height:56px}
    .sa-head{padding:15px}.sa-messages{padding:12px}
  }
  @media(prefers-reduced-motion:reduce){#sa-panel.open,#sa-slide-panel{animation:none;transition:none}#sa-launcher,.sa-product{transition:none}}
  `;

  document.head.appendChild(Object.assign(document.createElement('style'), { textContent: css }));

  /* ─── LAUNCHER ──────────────────────────────────────────────────────── */
  const launch = document.createElement('button');
  launch.id = 'sa-launcher'; launch.type = 'button';
  launch.setAttribute('aria-label', 'Open SA Embroidery chat');
  launch.innerHTML = '<svg width="27" height="27" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11.5a8.5 8.5 0 0 1-8.5 8.5 9 9 0 0 1-4-.9L3 21l1.9-4.5a9 9 0 0 1-.9-4A8.5 8.5 0 0 1 12.5 4H13a8.5 8.5 0 0 1 7 7.5Z"/></svg>';

  /* ─── MAIN CHAT PANEL ───────────────────────────────────────────────── */
  const panel = document.createElement('section');
  panel.id = 'sa-panel';
  panel.setAttribute('aria-label', 'SA Embroidery customer assistant');
  panel.innerHTML = `
    <div class="sa-head">
      <span class="sa-avatar">SA</span>
      <div class="sa-head-meta">
        <b>SA Embroidery Assistant</b>
        <small>Product &amp; Wholesale Support</small>
        <span class="sa-availability">Here to assist</span>
      </div>
      <button class="sa-x" type="button" aria-label="Close chat">×</button>
    </div>
    <div class="sa-actions">
      <button type="button" class="sa-chip" data-query="Show top selling products">Top Products</button>
      <button type="button" class="sa-chip" data-query="Show embroidery machine spare parts">Explore Parts</button>
      <button type="button" class="sa-chip" data-query="I need a wholesale quote">Get a Quote</button>
      <button type="button" class="sa-chip" data-query="Do you ship internationally?">Shipping</button>
      <button type="button" class="sa-chip" data-url="https://saembroidery.com/find-my-part">Find My Part ↗</button>
    </div>
    <div class="sa-messages" id="sa-messages" role="log" aria-live="polite"></div>
    <form class="sa-compose" id="sa-form">
      <input id="sa-input" maxlength="1200" placeholder="Ask about products, pricing, shipping…" aria-label="Your message" autocomplete="off" required>
      <button id="sa-send-btn" aria-label="Send message" type="submit">➤</button>
    </form>
    <div class="sa-foot">Need a specialist? <a id="sa-whatsapp" target="_blank" rel="noopener noreferrer">Contact our sales team</a></div>
  `;

  /* ─── SLIDE PANEL (left side) ───────────────────────────────────────── */
  const slidePanel = document.createElement('aside');
  slidePanel.id = 'sa-slide-panel';
  slidePanel.setAttribute('aria-label', 'Product image viewer');
  slidePanel.innerHTML = `
    <div class="sa-sp-head">
      <span class="sa-sp-title">Product Gallery</span>
      <button class="sa-sp-close" type="button" aria-label="Close gallery">×</button>
    </div>
    <div class="sa-sp-tabs" id="sa-sp-tabs"></div>
    <div class="sa-sp-slides" id="sa-sp-slides">
      <button class="sa-sp-nav sa-sp-prev" type="button" aria-label="Previous image">&#8249;</button>
      <button class="sa-sp-nav sa-sp-next" type="button" aria-label="Next image">&#8250;</button>
    </div>
    <div class="sa-sp-dots" id="sa-sp-dots"></div>
    <div class="sa-sp-info" id="sa-sp-info">
      <div class="sa-sp-name" id="sa-sp-name"></div>
      <div class="sa-sp-meta" id="sa-sp-meta"></div>
      <div class="sa-sp-price" id="sa-sp-price"></div>
      <button class="sa-cart-btn" id="sa-cart-btn" type="button">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
        Add to Cart
      </button>
    </div>
    <a class="sa-sp-wa" id="sa-sp-wa" target="_blank" rel="noopener noreferrer">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
      Order via WhatsApp
    </a>
  `;

  document.body.append(launch, panel, slidePanel);

  /* ─── DOM REFS ──────────────────────────────────────────────────────── */
  const messages   = panel.querySelector('#sa-messages');
  const form       = panel.querySelector('#sa-form');
  const input      = panel.querySelector('#sa-input');
  const send       = panel.querySelector('#sa-send-btn');
  const spTabs     = slidePanel.querySelector('#sa-sp-tabs');
  const spSlides   = slidePanel.querySelector('#sa-sp-slides');
  const spDots     = slidePanel.querySelector('#sa-sp-dots');
  const spName     = slidePanel.querySelector('#sa-sp-name');
  const spMeta     = slidePanel.querySelector('#sa-sp-meta');
  const spPrice    = slidePanel.querySelector('#sa-sp-price');
  const spCartBtn  = slidePanel.querySelector('#sa-cart-btn');
  const spWaLink   = slidePanel.querySelector('#sa-sp-wa');

  panel.querySelector('#sa-whatsapp').href = 'https://wa.me/' + cfg.whatsapp;

  /* ─── STATE ─────────────────────────────────────────────────────────── */
  const state = {
    products: [], loaded: false, history: [], busy: false,
    last: [], lastLanguage: 'en',
    slide: { products: [], activeProduct: 0, activeImage: 0 }
  };

  /* ─── UTILS ─────────────────────────────────────────────────────────── */
  const stripHtml = x => String(x || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  const parseJSON = x => { if (Array.isArray(x)) return x; try { const r = JSON.parse(x); return Array.isArray(r) ? r : [] } catch { return [] } };
  function parseSchema(x) { if (x && typeof x === 'object') return x; try { return JSON.parse(x || '{}') } catch { return {} } }
  function positive(x) { const n = Number(x); return Number.isFinite(n) && n > 0 ? n : null }

  function websitePrice(p) {
    const schema = parseSchema(p.schema_markup);
    const nodes = [schema, ...(Array.isArray(schema['@graph']) ? schema['@graph'] : [])];
    let offer = null;
    for (const node of nodes) {
      if (!node || typeof node !== 'object') continue;
      const offers = Array.isArray(node.offers) ? node.offers : [node.offers];
      for (const item of offers) {
        if (item && String(item.priceCurrency || '').toUpperCase() === 'USD') {
          offer = positive(item.price); if (offer !== null) break;
        }
      }
      if (offer !== null) break;
    }
    const base = positive(p.price), sale = positive(p.sale_price);
    const listed = (p.sale === true || p.sale === 'true' || p.sale === 1) && sale !== null && base !== null && sale < base ? sale : base;
    return offer !== null ? offer : listed;
  }

  function normalize(p) {
    const imgs = parseJSON(p.product_images);
    return {
      id: p.id, name: String(p.product_name || ''), slug: String(p.url_slug || ''),
      price: websitePrice(p), currency: 'USD', stock: Number(p.available_stock || 0),
      category: String(p.category_name || p.category1 || ''),
      short: stripHtml(p.short_description),
      description: stripHtml(p.description).slice(0, 1300),
      images: imgs.map(i => i.edited_url || i.url).filter(x => typeof x === 'string' && /^https:\/\//.test(x)),
      faqs: parseJSON(p.faqs), features: parseJSON(p.features), raw: p
    };
  }

  async function loadCatalog() {
    if (state.loaded) return state.products;
    const response = await fetch(cfg.productsApi, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw Error('Catalog temporarily unavailable');
    const data = await response.json();
    const items = Array.isArray(data) ? data : Array.isArray(data.data) ? data.data : [];
    state.products = items.filter(p => p.active !== false && p.archive !== true).map(normalize);
    state.loaded = true;
    return state.products;
  }

  function lang(q) {
    const roman = /\b(bhai|mujhe|mujhay|chahiye|chaiye|hai|hain|ka|ki|kya|kitna|kitne|rate|batao|btao|ap|aap|milay|milega|kr|bhej|bhejo|mery|pas|paas|wala|walay|karna|kro|delivery kab)\b/i;
    return roman.test(q) ? 'ur' : /\b(hello|hi|hey|thanks|thank you)\b/i.test(q) ? 'en' : state.lastLanguage;
  }

  function formatReply(el, text) {
    el.replaceChildren();
    const tokens = String(text || '').split(/(\[[^\]]+\]\(https?:\/\/[^\)]+\)|https?:\/\/[^\s\)\*]+|\*\*[^*\n]+\*\*|\*[^*\n]+\*)/g);
    for (const token of tokens) {
      if (!token) continue;
      const mdLink = token.match(/^\[([^\]]+)\]\((https?:\/\/[^\)]+)\)$/);
      if (mdLink) {
        const a = document.createElement('a');
        a.href = mdLink[2];
        a.textContent = mdLink[1];
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.className = 'sa-link';
        el.append(a);
        continue;
      }
      if (/^https?:\/\//i.test(token)) {
        const a = document.createElement('a');
        a.href = token;
        a.textContent = token;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.className = 'sa-link';
        el.append(a);
        continue;
      }
      const bold = token.match(/^\*\*([^*\n]+)\*\*$/);
      if (bold) {
        const strong = document.createElement('strong');
        strong.textContent = bold[1];
        el.append(strong);
        continue;
      }
      const italic = token.match(/^\*([^*\n]+)\*$/);
      if (italic) {
        const em = document.createElement('em');
        em.textContent = italic[1];
        el.append(em);
        continue;
      }
      el.append(document.createTextNode(token));
    }
  }

  function msg(t, cls = 'sa-bot') {
    const el = document.createElement('div'); el.className = 'sa-bubble ' + cls;
    if (cls === 'sa-bot') formatReply(el, t); else el.textContent = t;
    messages.append(el); messages.scrollTop = messages.scrollHeight; return el;
  }

  function whatsapp(msgText) { return 'https://wa.me/' + cfg.whatsapp + '?text=' + encodeURIComponent(msgText) }

  function productUrl(p) {
    const slug = String(p.slug || p.url_slug || '').replace(/^\/+/, '');
    return p.url && /^https:\/\//i.test(p.url)
      ? p.url
      : slug ? cfg.site.replace(/\/$/, '') + '/' + slug
      : cfg.site.replace(/\/$/, '') + '/products';
  }

  function productPrice(p) {
    if (typeof p.price === 'string' && p.price.trim()) {
      return p.price.toLowerCase().startsWith('starting from') ? p.price : ('Starting from ' + p.price);
    }
    const val = p.price_amount > 0 ? Number(p.price_amount) : positive(p.price);
    return val !== null ? 'Starting from $' + val.toFixed(2) : null;
  }

  function tokenise(s) {
    return String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').split(' ')
      .filter(x => x.length > 1 && !['the','and','for','with','please','need','want','show','parts','part','machine','mujhe','chahiye','hai','kya','ka','ki','rate','price','aap','mery','pas','bhai','bulk'].includes(x));
  }

  function matches(q) {
    const terms = tokenise(q); if (!terms.length) return [];
    return state.products.map(p => {
      let score = 0;
      const name = p.name.toLowerCase(), slug = p.slug.toLowerCase(), cat = p.category.toLowerCase(), desc = p.short.toLowerCase();
      for (const t of terms) {
        if (name.includes(t)) score += 5; if (slug.includes(t)) score += 4;
        if (cat.includes(t)) score += 1; if (desc.includes(t)) score += 1;
        if (String(p.id) === t) score += 20;
      }
      if (name.includes(q.toLowerCase())) score += 12;
      return { p, score };
    }).filter(v => v.score > 0).sort((a, b) => b.score - a.score).slice(0, 4).map(x => x.p);
  }

  /* ─── SLIDE PANEL LOGIC ─────────────────────────────────────────────── */

  function buildSlide(imgUrl, alt) {
    const div = document.createElement('div'); div.className = 'sa-sp-slide';
    const img = document.createElement('img'); img.src = imgUrl; img.alt = alt || ''; img.loading = 'lazy';
    div.append(img); return div;
  }

  function openSlidePanel(products) {
    if (!products || !products.length) return;
    const ss = state.slide;
    ss.products = products;
    ss.activeProduct = 0;
    ss.activeImage = 0;
    renderSlideProduct(0, 0);
    slidePanel.classList.add('sa-slide-open');
    requestAnimationFrame(() => requestAnimationFrame(() => slidePanel.classList.add('sa-slide-visible')));
  }

  function closeSlidePanel() {
    slidePanel.classList.remove('sa-slide-visible');
    setTimeout(() => slidePanel.classList.remove('sa-slide-open'), 350);
  }

  function renderSlideProduct(prodIdx, imgIdx) {
    const ss = state.slide;
    const products = ss.products;
    if (!products.length) return;
    const p = products[prodIdx];

    // Get images list — support both backend normalized & raw product shapes
    const allImgs = (p.images && p.images.length) ? p.images
      : (p.image_url ? [p.image_url] : []);

    // Build tabs
    spTabs.replaceChildren();
    products.forEach((prod, i) => {
      const tab = document.createElement('button');
      tab.type = 'button'; tab.className = 'sa-sp-tab' + (i === prodIdx ? ' active' : '');
      tab.textContent = prod.name.length > 18 ? prod.name.slice(0, 17) + '…' : prod.name;
      tab.addEventListener('click', () => renderSlideProduct(i, 0));
      spTabs.append(tab);
    });

    // Build slides (keep nav buttons, replace slides)
    const prevBtn = spSlides.querySelector('.sa-sp-prev');
    const nextBtn = spSlides.querySelector('.sa-sp-next');
    // Remove old slides
    spSlides.querySelectorAll('.sa-sp-slide').forEach(s => s.remove());

    if (!allImgs.length) {
      const placeholder = document.createElement('div');
      placeholder.style.cssText = 'display:flex;align-items:center;justify-content:center;height:100%;color:#8aa394;font-size:13px;';
      placeholder.textContent = 'No image available';
      spSlides.insertBefore(placeholder, nextBtn);
    } else {
      allImgs.forEach((url, i) => {
        const slide = buildSlide(url, p.name + ' image ' + (i + 1));
        if (i === imgIdx) slide.classList.add('active');
        spSlides.insertBefore(slide, nextBtn);
      });
    }

    // Dots
    spDots.replaceChildren();
    allImgs.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.type = 'button'; dot.className = 'sa-sp-dot' + (i === imgIdx ? ' active' : '');
      dot.setAttribute('aria-label', 'Image ' + (i + 1));
      dot.addEventListener('click', () => goToImage(i));
      spDots.append(dot);
    });

    // Hide nav if only 1 image
    prevBtn.style.display = allImgs.length > 1 ? '' : 'none';
    nextBtn.style.display = allImgs.length > 1 ? '' : 'none';

    // Product info
    spName.textContent = p.name || '';
    spMeta.textContent = [p.category, p.short_description || p.short].filter(Boolean).join(' · ').slice(0, 120) || '';
    const priceStr = productPrice(p);
    spPrice.textContent = priceStr ? priceStr + ' USD' : 'Price on request';
    spPrice.style.display = priceStr ? '' : 'none';

    // Cart btn → go to product page
    spCartBtn.onclick = () => window.open(productUrl(p), '_blank', 'noopener,noreferrer');
    spCartBtn.textContent = '';
    spCartBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg> Add to Cart`;

    // WA link
    spWaLink.href = whatsapp('Hello SA Embroidery, I want to order: ' + p.name + (priceStr ? ' (Price: ' + priceStr + ')' : ''));

    ss.activeProduct = prodIdx;
    ss.activeImage = imgIdx;
  }

  function goToImage(newIdx) {
    const ss = state.slide;
    const p = ss.products[ss.activeProduct];
    const allImgs = (p.images && p.images.length) ? p.images : (p.image_url ? [p.image_url] : []);
    if (!allImgs.length) return;
    newIdx = ((newIdx % allImgs.length) + allImgs.length) % allImgs.length;

    const slides = [...spSlides.querySelectorAll('.sa-sp-slide')];
    const dots = [...spDots.querySelectorAll('.sa-sp-dot')];
    const direction = newIdx > ss.activeImage ? 1 : -1;

    if (slides[ss.activeImage]) {
      slides[ss.activeImage].classList.remove('active');
      slides[ss.activeImage].classList.add('exit');
      setTimeout(() => { if (slides[ss.activeImage]) slides[ss.activeImage].classList.remove('exit'); }, 350);
    }
    if (dots[ss.activeImage]) dots[ss.activeImage].classList.remove('active');

    ss.activeImage = newIdx;

    if (slides[newIdx]) {
      slides[newIdx].style.transform = `translateX(${direction * 40}px)`;
      slides[newIdx].offsetHeight; // force reflow
      slides[newIdx].classList.add('active');
      slides[newIdx].style.transform = '';
    }
    if (dots[newIdx]) dots[newIdx].classList.add('active');
  }

  slidePanel.querySelector('.sa-sp-close').addEventListener('click', closeSlidePanel);
  slidePanel.querySelector('.sa-sp-prev').addEventListener('click', () => {
    const ss = state.slide;
    const p = ss.products[ss.activeProduct];
    const allImgs = (p && p.images && p.images.length) ? p.images : (p && p.image_url ? [p.image_url] : []);
    goToImage(ss.activeImage - 1);
  });
  slidePanel.querySelector('.sa-sp-next').addEventListener('click', () => {
    goToImage(state.slide.activeImage + 1);
  });

  /* ─── PRODUCT CARDS IN CHAT ─────────────────────────────────────────── */
  function showProducts(items) {
    if (!items || !items.length) return;
    const outer = document.createElement('div'); outer.className = 'sa-products';

    items.forEach((p, idx) => {
      const card = document.createElement('div'); card.className = 'sa-product';

      // Thumbnail
      const thumbSrc = (p.images && p.images[0]) || p.image_url;
      if (thumbSrc) {
        const img = document.createElement('img'); img.className = 'sa-product-thumb';
        img.src = thumbSrc; img.loading = 'lazy'; img.alt = p.name;
        card.append(img);
      } else {
        const ph = document.createElement('div'); ph.className = 'sa-product-thumb-placeholder';
        ph.textContent = '📦'; card.append(ph);
      }

      // Content
      const txt = document.createElement('div'); txt.className = 'sa-product-content';
      const title = document.createElement('strong'); title.textContent = p.name;
      const desc = document.createElement('small');
      desc.textContent = (p.short || p.short_description || '').slice(0, 80) || (p.category || 'Spare part');
      const priceStr = productPrice(p);
      const info = document.createElement('em');
      info.textContent = priceStr ? priceStr : (p.stock > 0 ? 'In stock' : 'Check availability');
      txt.append(title, desc, info);
      card.append(txt);

      // Action buttons
      const actions = document.createElement('div'); actions.className = 'sa-product-actions';

      const viewBtn = document.createElement('button'); viewBtn.type = 'button';
      viewBtn.className = 'sa-view-btn'; viewBtn.textContent = '🔍 View';
      viewBtn.addEventListener('click', () => openSlidePanel(items.slice(idx).concat(items.slice(0, idx))));
      actions.append(viewBtn);

      const cartBtn = document.createElement('button'); cartBtn.type = 'button';
      cartBtn.className = 'sa-mini-cart';
      cartBtn.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>Cart`;
      cartBtn.addEventListener('click', () => window.open(productUrl(p), '_blank', 'noopener,noreferrer'));
      actions.append(cartBtn);

      card.append(actions);
      outer.append(card);
    });

    messages.append(outer);
    messages.scrollTop = messages.scrollHeight;

    // Auto-open slide panel with first product
    openSlidePanel(items);
  }

  function quote(q) {
    const a = document.createElement('a');
    a.href = whatsapp('SA Embroidery product enquiry:\n' + q + (state.last.length ? '\nProducts: ' + state.last.map(p => p.name + ' (#' + p.id + ')').join(', ') : ''));
    a.target = '_blank'; a.rel = 'noopener noreferrer'; a.className = 'sa-quote-link';
    a.textContent = 'Continue on WhatsApp ↗'; messages.append(a);
  }

  async function askAI(q, products) {
    const body = {
      message: q, history: state.history.slice(-12), language: 'auto',
      products: products.map(p => ({ id: p.id, name: p.name, slug: p.slug, price: productPrice(p), stock: p.stock, category: p.category, description: p.short, images: p.images, features: p.features, faqs: p.faqs }))
    };
    const ctrl = new AbortController(); const timeout = setTimeout(() => ctrl.abort(), 12000);
    try {
      const res = await fetch(cfg.api, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: ctrl.signal });
      if (!res.ok) throw Error('AI endpoint error');
      const data = await res.json();
      return typeof data === 'string' ? { answer: data, products: [] } : data;
    } finally { clearTimeout(timeout); }
  }

  const shipping  = /ship|delivery|courier|dhl|fedex|international|export|dubai|uae|saudi|ksa|uk|usa|bhej|country/i;
  const wholesale = /bulk|wholesale|discount|quotation|quote|order|supplier|resell|quantity|kitne pieces|kitnay|rate|price|cost|qeemat/i;
  const identify  = /photo|picture|image|identify|broken|model|compatible|part number|find my part|tasveer|tasvir/i;
  const general   = /^(h+i+|h+y+|hey+|hello+|assalam|salam|aoa|thanks|thank you|ok|okay|how are (?:you|u)|how r u)[\s!.?]*$/i;

  /* ─── SEND MESSAGE ──────────────────────────────────────────────────── */
  async function sendMessage(q) {
    q = String(q || '').trim(); if (!q || state.busy) return;
    state.busy = true; send.disabled = true; input.value = '';
    state.lastLanguage = lang(q); const ur = state.lastLanguage === 'ur';
    msg(q, 'sa-user');
    const thinking = msg(ur ? 'Aapki request check kar raha hoon…' : 'Checking your request…');

    let products = [];
    if (state.products.length) {
      products = matches(q);
    } else {
      loadCatalog().catch(() => {});
    }
    state.last = products;

    let answer = null; let verifiedProducts = []; let isRefusal = false; let actionUrl = null;
    try {
      const response = await askAI(q, products);
      answer = response?.answer || response?.reply || null;
      verifiedProducts = Array.isArray(response?.products) ? response.products : [];
      isRefusal = response?.type === 'refusal' || response?.intent === 'off_topic';
      actionUrl = response?.action_url || null;
    } catch (e) { console.info('AI service unavailable', e.message); }

    const isFindPart = /\b(find\s+my\s+part|find\s+part|part\s+finder|part\s+dhund)\b/i.test(q);
    if (isFindPart || actionUrl) {
      const targetUrl = actionUrl || 'https://saembroidery.com/find-my-part';
      window.open(targetUrl, '_blank', 'noopener,noreferrer');
      if (!answer) {
        answer = ur
          ? 'Hamari website ka **Find My Part** tool open kar diya gaya hai:\n\n' + targetUrl
          : 'Opening our **Find My Part** tool on the website:\n\n' + targetUrl;
      }
    }

    if (!answer) {
      const offTopic = /\b(python|javascript|typescript|c\+\+|java|c#|ruby|php|rust|golang|html|css|coding|code|programmer|programming|recipe|biryani|cake|president|prime minister|photosynthesis|cricket|messi|football|weather|joke|poem|essay|story)\b/i;
      if (offTopic.test(q)) {
        isRefusal = true;
        answer = ur
          ? 'Main sirf SA Embroidery ka AI assistant hoon. Main sirf embroidery aur sewing machine spare parts, products, qeemat, orders, aur store services ke mutaliq madad kar sakta hoon.'
          : 'I am the SA Embroidery assistant. I can only help with embroidery and sewing machine spare parts, products, pricing, orders, and store services.';
      } else if (products.length) {
        const p = products[0];
        answer = ur
          ? `${p.name} listed hai hamare catalog mein. ${p.short || ''}\n\nPrice: ${productPrice(p) || 'quotation par confirm hogi'}. Stock: ${p.stock}. Machine model aur quantity share karein.`
          : `I found ${p.name} in our catalog. ${p.short || ''}\n\nListed price: ${productPrice(p) || 'available on request'}. Stock: ${p.stock}. Share your machine model and quantity for a confirmed quote.`;
      } else if (general.test(q)) {
        answer = ur ? 'Assalam-o-alaikum! SA Embroidery mein khush aamdeed. Kya madad kar sakta hoon?' : 'Welcome to SA Embroidery! How can I assist you today?';
      } else if (shipping.test(q)) {
        answer = ur ? 'Ji, SA Embroidery international shipping handle karta hai. Destination, item aur quantity bata dein.' : 'We support international shipping. Please share your destination, product and quantity.';
      } else if (wholesale.test(q)) {
        answer = ur ? 'Bulk quotation ke liye product name, quantity aur delivery city bhej dein.' : 'For wholesale enquiries, please share the product name, quantity and delivery country.';
      } else if (identify.test(q)) {
        answer = ur ? 'Machine brand, model aur part number batayein. Photo WhatsApp par share kar sakte hain.' : 'Please share the machine brand, model and part number. You can send a photo via WhatsApp.';
      } else {
        answer = ur ? 'Aapki request samajhna chahta hoon. Machine model, part number ya product category share karein.' : 'Could you share a part number, machine model or product category? Our team can also assist through WhatsApp.';
      }
    }

    formatReply(thinking, answer);
    state.history.push({ role: 'user', content: q }, { role: 'assistant', content: answer });

    if (!isRefusal) {
      const toShow = verifiedProducts.length ? verifiedProducts
        : (products.length && !general.test(q) && !shipping.test(q)) ? products.slice(0, 3)
        : [];
      if (toShow.length) showProducts(toShow);
      if (wholesale.test(q) || identify.test(q) || shipping.test(q) || toShow.length) quote(q);
    }
    messages.scrollTop = messages.scrollHeight;
    state.busy = false; send.disabled = false; input.focus();
  }

  /* ─── EVENT LISTENERS ───────────────────────────────────────────────── */
  launch.addEventListener('click', () => {
    panel.classList.add('open');
    launch.style.display = 'none';
    launch.setAttribute('aria-expanded', 'true');
    input.focus();
  });
  panel.querySelector('.sa-x').addEventListener('click', () => {
    panel.classList.remove('open');
    launch.style.display = 'grid';
    launch.setAttribute('aria-expanded', 'false');
    launch.focus();
    closeSlidePanel();
  });
  form.addEventListener('submit', e => {
    e.preventDefault();
    e.stopPropagation();
    sendMessage(input.value);
  });
  panel.querySelectorAll('.sa-chip').forEach(b => b.addEventListener('click', () => {
    if (b.dataset.url) {
      window.open(b.dataset.url, '_blank', 'noopener,noreferrer');
      msg(b.textContent.replace('↗', '').trim(), 'sa-user');
      const ur = state.lastLanguage === 'ur';
      msg(ur
        ? 'Find My Part tool open kar diya gaya hai: ' + b.dataset.url
        : 'Opening Find My Part tool: ' + b.dataset.url);
      return;
    }
    if (b.dataset.query) sendMessage(b.dataset.query);
  }));

  /* ─── WELCOME MESSAGE ───────────────────────────────────────────────── */
  const welcome = document.createElement('div'); welcome.className = 'sa-welcome';
  const wKicker = document.createElement('div'); wKicker.className = 'sa-welcome-kicker'; wKicker.textContent = 'SA EMBROIDERY';
  const wTitle  = document.createElement('div'); wTitle.className  = 'sa-welcome-title';  wTitle.textContent  = 'Welcome. How can we help?';
  const wRule   = document.createElement('span'); wRule.className   = 'sa-welcome-rule';
  const wDesc   = document.createElement('div'); wDesc.className   = 'sa-welcome-desc';   wDesc.textContent   = 'Find embroidery and sewing machine spare parts, threads, and accessories. Ask about pricing, shipping, and wholesale orders.';
  welcome.append(wKicker, wTitle, wRule, wDesc); messages.append(welcome);

  /* ─── PAGE PRODUCT PREVIEW (if #sa-live-products exists) ───────────── */
  async function preview() {
    const root = document.getElementById('sa-live-products'); if (!root) return;
    try {
      const all = await loadCatalog(); root.replaceChildren();
      for (const p of all.filter(p => p.images.length).slice(0, 4)) {
        const card = document.createElement('div'); card.className = 'card';
        const img = document.createElement('img'); img.className = 'card-img'; img.src = p.images[0]; img.alt = p.name; img.loading = 'lazy';
        const body = document.createElement('div'); body.className = 'card-body';
        const name = document.createElement('h3'); name.className = 'card-title'; name.textContent = p.name;
        const cat  = document.createElement('div'); cat.className  = 'card-cat';   cat.textContent  = p.category;
        const row  = document.createElement('div'); row.className  = 'card-price-row';
        const stock = document.createElement('span'); stock.className = 'card-price'; stock.textContent = p.stock > 0 ? 'Stock listed: ' + p.stock : 'Request availability';
        const btn = document.createElement('button'); btn.className = 'card-btn'; btn.textContent = 'Ask assistant';
        btn.addEventListener('click', () => { if (!panel.classList.contains('open')) launch.click(); sendMessage(p.name + ' part number ' + p.id); });
        row.append(stock, btn); body.append(name, cat, row); card.append(img, body); root.append(card);
      }
    } catch { root.textContent = 'Browse the full product catalog on saembroidery.com.'; }
  }
  preview();

})();