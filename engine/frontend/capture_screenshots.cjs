const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  // High quality mobile viewport (iPhone 14 Pro style: 430 x 932 @ 3x)
  const page = await browser.newPage({ 
    viewport: { width: 450, height: 950 }, 
    deviceScaleFactor: 2 
  });
  
  console.log('Capturing Hero...');
  await page.goto('https://violett.com.ar/pilates', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'c:/Users/Alex/Downloads/Prueba video ia/remotion-studio-pro/public/violett/real_hero_mobile.png' });

  console.log('Capturing Experiencia (55 + 5 min)...');
  const exp = await page.$('#experiencia');
  if (exp) {
    await exp.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'c:/Users/Alex/Downloads/Prueba video ia/remotion-studio-pro/public/violett/real_experiencia_mobile.png' });
  }

  console.log('Capturing Membresias...');
  const mem = await page.$('#membresias');
  if (mem) {
    await mem.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'c:/Users/Alex/Downloads/Prueba video ia/remotion-studio-pro/public/violett/real_membresias_mobile.png' });
  }

  console.log('Capturing Metodo...');
  const met = await page.$('#metodo');
  if (met) {
    await met.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'c:/Users/Alex/Downloads/Prueba video ia/remotion-studio-pro/public/violett/real_metodo_mobile.png' });
  }

  console.log('Capturing Login Portal...');
  await page.goto('https://violett.com.ar/pilates/login', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'c:/Users/Alex/Downloads/Prueba video ia/remotion-studio-pro/public/violett/real_login_mobile.png' });

  console.log('All real mobile screenshots successfully captured!');
  await browser.close();
})().catch(e => {
  console.error(e);
  process.exit(1);
});
