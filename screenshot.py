import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import os
import glob
import shutil
from jinja2 import Template
from pytz import timezone


sites = [
        {
            'url': 'https://kurier.at',
            'name': 'kurier',
            'button_selector': 'button#didomi-notice-agree-button',
            'output_dir': 'screenshots'
        },
        {
            'url': 'https://derstandard.at',
            'name': 'derstandard',
            'button_selector': 'button.sp_choice_type_11',
            'frame_selector': '#sp_message_iframe_1030279',
            'output_dir': 'screenshots'
        },
        {
            'url': 'https://krone.at',
            'name': 'krone',
            'button_selector': 'button#didomi-notice-agree-button',
            'output_dir': 'screenshots'
        },
        {
            'url': 'https://heute.at',
            'name': 'heute',
            'button_selector': 'button.sp_choice_type_11',
            'frame_selector': '#sp_message_iframe_1152937',
            'output_dir': 'screenshots'
        },
        {
            'url': 'https://diepresse.com',
            'name': 'diepresse',
            'button_selector': 'button#didomi-notice-agree-button',
            'output_dir': 'screenshots'
        },
        {
            'url': 'https://oe24.at',
            'name': 'o24',
            'button_selector': 'button.sp_choice_type_11',
            'frame_selector': '#sp_message_iframe_1221612',
            'output_dir': 'screenshots'
        },
        {
            'url': 'https://orf.at',
            'name': 'orf',
            'button_selector': 'button#didomi-notice-agree-button',
            'output_dir': 'screenshots'
        },
        {
            'url': 'https://kleinezeitung.at',
            'name': 'kleinezeitung',
            'button_selector': 'button#didomi-notice-agree-button',
            'output_dir': 'screenshots'
        }
    ]

TIMELINE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>24h Website Timeline</title>
    <style>
        body { 
            margin: 0;
            font-family: Arial, sans-serif;
        }
        .timeline-controls {
            position: sticky;
            top: 0;
            background: white;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 100;
        }
        .screenshots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .site-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background: white;
        }
        .device-views {
            display: grid;
            gap: 15px;
        }
        .device-view img {
            width: 100%;
            height: auto;
            border: 1px solid #eee;
            border-radius: 4px;
            transition: transform 0.2s;
            cursor: pointer;
        }
        .device-view img:hover {
            transform: scale(1.02);
        }
        /* Modal styles */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            padding: 20px;
            box-sizing: border-box;
        }
        .modal-content {
            max-width: 90%;
            max-height: 90vh;
            margin: auto;
            display: block;
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
        .modal-caption {
            margin: auto;
            display: block;
            width: 80%;
            max-width: 700px;
            text-align: center;
            color: #ccc;
            padding: 10px 0;
            height: 150px;
        }
        /* Controls */
        select {
            padding: 8px;
            margin-right: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        h3 { margin-top: 0; }
        .timestamp { 
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="timeline-controls">
        <h1>Startseiten</h1>
        <div>
            <select id="timestampSelect">
                {% for ts in timestamps %}
                <option value="{{ ts }}">{{ ts }}</option>
                {% endfor %}
            </select>
            <select id="deviceFilter">
                <option value="all">All Devices</option>
                <option value="desktop">Desktop</option>
                <option value="mobile">Mobile</option>
            </select>
        </div>
        <p class="timestamp">Generated at: {{ generated_at }}</p>
    </div>
    
    <div class="screenshots-grid">
        {% for site in sites %}
        <div class="site-card">
            <h3>{{ site.name }}</h3>
            <p><a href="{{ site.url }}" target="_blank">{{ site.url }}</a></p>
            <div class="device-views">
                {% for device in ['desktop', 'mobile'] %}
                <div class="device-view" data-device="{{ device }}">
                    <h4>{{ device|title }}</h4>
                    <img src="archive/{{ timestamps[0] }}/{{ site.name }}_{{ device }}.jpeg" 
                        class="screenshot-img"
                        data-site="{{ site.name }}"
                        data-device="{{ device }}"
                        onclick="openModal(this)">
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Modal -->
    <div id="imageModal" class="modal">
        <span class="modal-close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
        <div id="modalCaption" class="modal-caption"></div>
    </div>

    <script>
        const modal = document.getElementById('imageModal');
        const modalImg = document.getElementById('modalImage');
        const captionText = document.getElementById('modalCaption');

        function openModal(img) {
            modal.style.display = "flex";
            modalImg.src = img.src;
            captionText.innerHTML = `${img.dataset.site} - ${img.dataset.device}`;
        }

        function closeModal() {
            modal.style.display = "none";
        }

        // Close modal when clicking outside the image
        modal.onclick = function(event) {
            if (event.target === modal) {
                closeModal();
            }
        }

        // Update screenshots when timestamp changes
        document.getElementById('timestampSelect').addEventListener('change', (e) => {
            const timestamp = e.target.value;
            document.querySelectorAll('.screenshot-img').forEach(img => {
                const site = img.dataset.site;
                const device = img.dataset.device;
                img.src = `archive/${timestamp}/${site}_${device}.jpeg`;
            });
        });

        // Device filter
        document.getElementById('deviceFilter').addEventListener('change', (e) => {
            const device = e.target.value;
            document.querySelectorAll('.device-view').forEach(view => {
                if (device === 'all' || view.dataset.device === device) {
                    view.style.display = 'block';
                } else {
                    view.style.display = 'none';
                }
            });
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""

async def take_screenshot(config: dict, device_type: str = 'desktop'):
    """
    Take screenshot with configuration dictionary containing:
    {
        'url': str,  # The URL of the website to capture
        'name': str,  # The name of the website (used for naming the screenshot file)
        'button_selector': str,  # The CSS selector for the consent button
        'frame_selector': str (optional),  # The CSS selector for the iframe containing the consent button (if any)
        'output_dir': str (optional)  # The directory where the screenshot will be saved (default is current directory)
    }
    device_type: 'desktop' or 'mobile'
    """
    async with async_playwright() as p:
        try:
            # Device configurations
            devices = {
                'desktop': {
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                'mobile': {
                    **p.devices['iPhone 13'],  # Use Playwright's predefined device
                }
            }
            
            browser = await p.chromium.launch()
            context = await browser.new_context(**devices[device_type])
            page = await context.new_page()
            
            output_dir = config.get('output_dir', '.')
            output_path = f"{output_dir}/{config['name']}_{device_type}.jpeg"
            
            # Wait for page load
            # await page.goto(config['url'], wait_until='networkidle')
            # await page.wait_for_load_state('domcontentloaded')
            
            try:
                await page.goto(
                    config['url'],
                    wait_until='domcontentloaded',
                    timeout=20000
                )
                await page.wait_for_timeout(2000)
            
                async def try_click_consent():
                    try:
                        if config.get('frame_selector'):
                            frame = page.frame_locator(config['frame_selector'])
                            await frame.locator(config['button_selector']).click(timeout=2000)
                        else:
                            await page.locator(config['button_selector']).click(timeout=2000)
                        return True
                    except Exception as e:
                        print(f"Click attempt failed for {config['name']} ({device_type}): {str(e)}")
                        return False
                
                # Retry mechanism
                max_retries = 5
                for i in range(max_retries):
                    if await try_click_consent():
                        print(f"Successfully clicked consent for {config['name']} ({device_type}) on try {i+1}")
                        break
                    print(f"Attempt {i+1} failed for {config['name']} ({device_type}), waiting...")
                    await page.wait_for_timeout(2000)
                
                # Take full page screenshot
                await page.wait_for_timeout(5000)
                await page.screenshot(path=output_path, type='jpeg', quality=50)
            except asyncio.TimeoutError:
                print(f"Timeout error capturing screenshot for {config['name']} ({device_type})")
            except Exception as e:
                print(f"Error capturing screenshot for {config['name']} ({device_type}): {str(e)}")
        finally:
            await browser.close()

async def take_timestamped_screenshots(sites):
    """
    Take timestamped screenshots for a list of sites.

    Args:
        sites (list): A list of dictionaries, each containing the configuration for a site.
    """
    # Create timestamp-based directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    screenshots_dir = f'archive/{timestamp}'
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Take screenshots
    tasks = []
    for site in sites:
        for device in ['desktop', 'mobile']:
            screenshot_path = f"{screenshots_dir}/{site['name']}_{device}.jpeg"
            site.update({'output_dir': screenshots_dir})
            tasks.append(take_screenshot(site, device))
    
    await asyncio.gather(*tasks)
    return timestamp

def cleanup_old_screenshots():
    """Remove screenshots older than 48 hours"""
    cutoff = datetime.now() - timedelta(hours=48)
    for dir_path in glob.glob('archive/*'):
        dir_time = datetime.strptime(os.path.basename(dir_path), '%Y%m%d_%H%M')
        if dir_time < cutoff:
            shutil.rmtree(dir_path)

def generate_timeline_report(sites):
    # Get last 48h of timestamps (192 entries for 15min intervals)
    timestamps = sorted(glob.glob('archive/*'), reverse=True)[:192]
    timestamps = [os.path.basename(t) for t in timestamps]
    
    if not timestamps:
        print("No archives found")
        return
    
    template = Template(TIMELINE_HTML)
    # Specify the timezone
    tz = timezone('Europe/Vienna')

    html_content = template.render(
        timestamps=timestamps,
        sites=sites,
        generated_at=datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    )
    
    with open('timeline_report.html', 'w') as f:
        f.write(html_content)

async def main():
    # Take new screenshots
    timestamp = await take_timestamped_screenshots(sites)
    print(f"Screenshots captured at: {timestamp}")
    
    # Generate updated report
    generate_timeline_report(sites)
    print("Timeline report updated")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())