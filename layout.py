import streamlit as st
import os
import base64

def apply_custom_css(theme="light"):
    st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
            """, unsafe_allow_html=True)
    """Applies custom CSS from `style.css` and handles light/dark mode."""
    css_path = "style.css"
    try:
        if os.path.exists(css_path):
            with open(css_path) as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        else:
            st.warning("Custom CSS file not found.")
    except Exception as e:
        st.error(f"CSS load error: {e}")

def render_header():
    """Render the responsive header with navigation and dropdowns."""
    logo_path = "static/Logo.png"
    fallback_logo = "https://cdn-icons-png.flaticon.com/512/1489/1489730.png"

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img:
            logo_base64 = base64.b64encode(img.read()).decode("utf-8")
            logo_src = f"data:image/png;base64,{logo_base64}"
    else:
        logo_src = fallback_logo

    nav_items = [
        {"name": "Home", "href": "/", "active": st.session_state.get("redirect_to", "") == "app.py"},
        {
            "name": "Services",
            "dropdown": [
                {"name": "Diabetes Detection", "href": "/diabetes"},
                {"name": "Parkinson's Detection", "href": "/parkinsons"},
                {"name": "Pneumonia Detection", "href": "/pneumonia"}
            ]
        },
        {"name": "About", "href": "/about", "active": st.session_state.get("redirect_to", "").endswith("about.py")},
        {"name": "Contact", "href": "/contact", "active": st.session_state.get("redirect_to", "").endswith("contact.py")},
        {"name": "Privacy", "href": "/privacy", "active": st.session_state.get("redirect_to", "").endswith("privacy.py")},
        {"name": "Log in / Sign up", "href": "/login", "class": "cta-button", "active": st.session_state.get("redirect_to", "").endswith("login.py")}
    ]

    # Build nav HTML
    nav_html = "<nav class='nav-menu' role='navigation'>"
    for item in nav_items:
        if "dropdown" in item:
            nav_html += f"""
            <div class='dropdown'>
                <a href='#' class='nav-item' aria-haspopup='true'>{item['name']}</a>
                <div class='dropdown-content'>
                    {''.join([f"<a href='{sub['href']}' class='dropdown-item'>{sub['name']}</a>" for sub in item['dropdown']])}
                </div>
            </div>
            """
        else:
            active_class = "active" if item.get("active", False) else ""
            nav_html += f"<a href='{item['href']}' class='nav-item {item.get('class', '')} {active_class}'>{item['name']}</a>"
    nav_html += "</nav>"

    # JavaScript for mobile nav and dropdown handling
    js_code = """
    <script>
    function toggleMenu() {
        const nav = document.querySelector('.nav-menu');
        nav.classList.toggle('active');
    }
    document.addEventListener('click', function(event) {
        document.querySelectorAll('.dropdown-content').forEach(dd => {
            if (!dd.parentElement.contains(event.target)) {
                dd.style.display = 'none';
            }
        });
    });
    document.querySelectorAll('.dropdown').forEach(d => {
        d.addEventListener('mouseenter', function() {
            this.querySelector('.dropdown-content').style.display = 'block';
        });
        d.addEventListener('mouseleave', function() {
            this.querySelector('.dropdown-content').style.display = 'none';
        });
    });
    </script>
    """

    st.markdown(f"""
    <header class="header" role="banner">
        <div class="logo-container">
            <img src="{logo_src}" alt="Logo" class="logo">
            <span style="font-weight: 600;">Didar AI/ML Solutions</span>
        </div>
        <button class="hamburger" onclick="toggleMenu()" aria-label="Toggle navigation">☰</button>
        {nav_html}
    </header>
    {js_code}
    """, unsafe_allow_html=True)

def render_footer():
    """Render the footer with contact and social links."""
    footer_links = [
        {"name": "Contact Us", "href": "/contact"},
        {"name": "Privacy Policy", "href": "/privacy"},
        {"name": "Terms of Service", "href": "/terms"}
    ]

    social_links = [
        {"icon": "🐦", "href": "https://twitter.com/healthaisuperapp", "name": "Twitter"},
        {"icon": "💼", "href": "https://linkedin.com/company/healthaisuperapp", "name": "LinkedIn"},
        {"icon": "💻", "href": "https://github.com/didar-ali", "name": "GitHub"}
    ]

    contact_info = [
        {"icon": "📧", "text": "support@healthaisuperapp.com", "href": "mailto:support@healthaisuperapp.com"},
        {"icon": "📍", "text": "Peshawar, Pakistan"}
    ]

    links_html = "".join([f"<a href='{l['href']}' class='footer-link'>{l['name']}</a>" for l in footer_links])
    socials_html = "".join([f"<a href='{s['href']}' class='social-link'>{s['icon']}</a>" for s in social_links])
    contact_html = "".join([
        f"<p>{c['icon']} {f'<a href={c['href']} class=footer-link>{c['text']}</a>' if 'href' in c else c['text']}</p>" 
        for c in contact_info
    ])

    st.markdown(f"""
    <footer class="footer" role="contentinfo">
        <div class="footer-content">
            <div class="footer-links">{links_html}</div>
            <div class="social-links">{socials_html}</div>
            <p class="copyright">© 2025 Didar AI/ML Solutions</p>
            {contact_html}
        </div>
    </footer>
    """, unsafe_allow_html=True)

