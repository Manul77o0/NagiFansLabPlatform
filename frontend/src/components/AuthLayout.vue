<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  formLabel: {
    type: String,
    required: true
  },
  showIntro: {
    type: Boolean,
    default: true
  }
})
</script>

<template>
  <div class="auth-page">
    <header class="auth-header">
      <a class="brand" href="/" aria-label="NagiFans Lab ホーム">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path d="M7 23.5V8.5l18 15V8.5" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="25" cy="8" r="2" fill="currentColor" />
          </svg>
        </span>
        <span class="brand-name">NagiFans <strong>Lab</strong></span>
      </a>
      <span class="header-label"><span class="header-dot"></span>MEMBERS AREA</span>
    </header>

    <main class="auth-main" :class="{ 'auth-main--centered': !showIntro }">
      <aside v-if="showIntro" class="auth-intro">
        <p class="intro-eyebrow"><span class="intro-eyebrow-mark">✳</span>{{ eyebrow }}</p>
        <h1>{{ title }}</h1>
        <p class="intro-description">{{ description }}</p>

        <div class="network-art" aria-hidden="true">
          <span class="network-orbit orbit-one"></span>
          <span class="network-orbit orbit-two"></span>
          <span class="network-node node-one"></span>
          <span class="network-node node-two"></span>
          <span class="network-node node-three"></span>
          <div class="network-center">
            <svg viewBox="0 0 48 48" fill="none">
              <path d="M24 5 39 11v11c0 10-6.3 17.1-15 21-8.7-3.9-15-11-15-21V11L24 5Z" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" />
              <path d="m17.5 24 4.2 4.2 9-9" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </div>
          <div class="network-card">
            <span class="network-card-label">YOUR WORKSPACE</span>
            <strong>つながる、ツールの入口。</strong>
            <span class="network-card-status"><span></span>アカウント認証</span>
          </div>
        </div>

        <div class="intro-note">
          <span class="note-icon" aria-hidden="true">↗</span>
          <span>あなたのアカウントから、必要なツールへ。</span>
        </div>
      </aside>

      <section class="auth-panel" :aria-label="formLabel">
        <div class="auth-card">
          <div class="card-topline">
            <span class="card-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 3 19 6v5.2c0 4.8-3 8.2-7 10.1-4-1.9-7-5.3-7-10.1V6l7-3Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
                <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <span>{{ formLabel }}</span>
          </div>
          <slot></slot>
          <div v-if="$slots.footer" class="auth-card-footer">
            <slot name="footer"></slot>
          </div>
        </div>
        <p class="auth-copyright">© NagiFans Lab <span>·</span> A calmer way to connect.</p>
      </section>
    </main>
  </div>
</template>

<style scoped>
.auth-page {
  --auth-ink: #1d3448;
  --auth-muted: #748597;
  --auth-blue: #2874c8;
  min-height: 100vh;
  box-sizing: border-box;
  padding: 0 6.1%;
  overflow: hidden;
  color: var(--auth-ink);
  background:
    radial-gradient(ellipse at 9% 92%, rgba(216, 238, 247, 0.6), transparent 32%),
    #f5f8fb;
  font-family: "Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
}

.auth-header {
  height: 94px;
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: var(--auth-ink);
  text-decoration: none;
}

.brand-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  color: #fff;
  background: linear-gradient(145deg, #3895d1, #236ab6);
  box-shadow: 0 5px 12px rgba(40, 116, 200, 0.19);
}

.brand-mark svg {
  width: 24px;
  height: 24px;
}

.brand-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.035em;
}

.brand-name strong {
  color: var(--auth-blue);
  font-weight: 750;
}

.header-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8393a2;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.header-dot,
.network-card-status span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #52b69a;
  box-shadow: 0 0 0 3px rgba(82, 182, 154, 0.12);
}

.auth-main {
  box-sizing: border-box;
  max-width: 1120px;
  min-height: calc(100vh - 94px);
  margin: 0 auto;
  padding: 28px 0 56px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(390px, 0.86fr);
  align-items: center;
  gap: clamp(48px, 8vw, 118px);
}

.auth-main--centered {
  grid-template-columns: minmax(390px, 460px);
  justify-content: center;
}

.auth-intro {
  position: relative;
  padding: 0 0 18px;
}

.intro-eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 0 22px;
  color: #4384ad;
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 0.15em;
}

.intro-eyebrow-mark {
  display: grid;
  width: 23px;
  height: 23px;
  place-items: center;
  border-radius: 7px;
  color: #3d91bd;
  background: #e2f2f7;
  font-size: 15px;
  letter-spacing: 0;
}

.auth-intro h1 {
  width: 450px;
  max-width: 100%;
  margin: 0;
  color: #20394f;
  font-size: clamp(34px, 4vw, 48px);
  font-weight: 720;
  letter-spacing: -0.055em;
  line-height: 1.33;
}

.intro-description {
  max-width: 425px;
  margin: 20px 0 0;
  color: #718496;
  font-size: 14px;
  line-height: 1.95;
}

.network-art {
  position: relative;
  height: 260px;
  max-width: 450px;
  margin: 22px 0 4px;
}

.network-orbit {
  position: absolute;
  top: 50%;
  left: 45%;
  border: 1px solid rgba(98, 167, 193, 0.2);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.orbit-one {
  width: 230px;
  height: 230px;
}

.orbit-two {
  width: 170px;
  height: 170px;
  border-style: dashed;
  border-color: rgba(98, 167, 193, 0.28);
}

.network-center {
  position: absolute;
  top: 50%;
  left: 45%;
  width: 76px;
  height: 76px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 24px;
  color: #fff;
  background: linear-gradient(145deg, #62b9ce, #347fb3);
  box-shadow: 0 14px 35px rgba(43, 123, 164, 0.23), inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform: translate(-50%, -50%) rotate(-7deg);
}

.network-center svg {
  width: 42px;
  height: 42px;
  transform: rotate(7deg);
}

.network-node {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 3px solid #f5f8fb;
  border-radius: 50%;
  background: #6bb5c2;
  box-shadow: 0 0 0 1px rgba(87, 161, 181, 0.25);
}

.node-one { top: 18%; left: 43%; }
.node-two { top: 66%; left: 14%; background: #91bdd1; }
.node-three { top: 69%; left: 74%; background: #5da7bf; }

.network-card {
  position: absolute;
  top: 50%;
  left: 66%;
  width: 205px;
  box-sizing: border-box;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  border: 1px solid rgba(223, 233, 239, 0.95);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 15px 40px rgba(60, 94, 119, 0.1);
  transform: translateY(-14%);
}

.network-card-label {
  color: #96a6b3;
  font-size: 8px;
  font-weight: 750;
  letter-spacing: 0.13em;
}

.network-card strong {
  color: #36546c;
  font-size: 12px;
  font-weight: 700;
}

.network-card-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7d8f9d;
  font-size: 9px;
}

.network-card-status span {
  width: 6px;
  height: 6px;
}

.intro-note {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #8394a2;
  font-size: 11px;
}

.note-icon {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border: 1px solid #dce8ee;
  border-radius: 7px;
  color: #5b9eb6;
  background: rgba(255, 255, 255, 0.65);
  font-size: 13px;
}

.auth-panel {
  width: 100%;
}

.auth-card {
  box-sizing: border-box;
  width: 100%;
  padding: 38px 40px 32px;
  border: 1px solid #e8eef3;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 22px 60px rgba(36, 68, 93, 0.08), 0 2px 6px rgba(36, 68, 93, 0.025);
}

.card-topline {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 27px;
  color: #7d91a1;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.11em;
}

.card-icon {
  width: 31px;
  height: 31px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  color: #377db9;
  background: #eef6fb;
}

.card-icon svg {
  width: 20px;
  height: 20px;
}

.auth-card-footer {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #edf1f4;
}

.auth-copyright {
  margin: 19px 0 0;
  color: #a0adb8;
  font-size: 10px;
  text-align: center;
  letter-spacing: 0.015em;
}

.auth-copyright span {
  margin: 0 4px;
  color: #ccd5dc;
}

@media (max-width: 920px) {
  .auth-page { padding: 0 5%; }
  .auth-main {
    max-width: 560px;
    min-height: auto;
    padding: 40px 0 54px;
    grid-template-columns: minmax(0, 1fr);
    gap: 30px;
  }
  .auth-main--centered { grid-template-columns: minmax(0, 1fr); }
  .auth-intro { padding-bottom: 0; }
  .auth-intro h1 { max-width: 100%; font-size: 37px; }
  .intro-description { margin-top: 12px; }
  .network-art,
  .intro-note { display: none; }
}

@media (max-width: 540px) {
  .auth-page { padding: 0 20px; }
  .auth-header { height: 72px; }
  .brand-mark { width: 33px; height: 33px; }
  .header-label { font-size: 8px; }
  .auth-main { padding: 33px 0 40px; gap: 23px; }
  .intro-eyebrow { margin-bottom: 14px; font-size: 9px; }
  .intro-eyebrow-mark { width: 21px; height: 21px; }
  .auth-intro h1 { font-size: 31px; }
  .intro-description { font-size: 12px; }
  .auth-card { padding: 28px 23px 24px; border-radius: 13px; }
  .card-topline { margin-bottom: 23px; }
}
</style>
