const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();

    page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
    page.on('pageerror', error => console.log('BROWSER ERROR:', error.message));
    
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

    // Login using credentials
    console.log("Logging in as Admin...");
    await page.type('input[type="email"]', 'admin@yagel-yaakov.edu');
    await page.type('input[type="password"]', 'AdminPassword123!');
    await page.click('button[type="submit"]');

    // Wait for navigation or network
    await new Promise(r => setTimeout(r, 3000));
    
    console.log("Done waiting.");
    await browser.close();
})();
