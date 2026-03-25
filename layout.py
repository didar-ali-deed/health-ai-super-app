import streamlit as st
import os
import base64

def apply_custom_css(theme="light"):
    """Applies custom CSS from `style.css` and handles light/dark mode."""
    st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
            """, unsafe_allow_html=True)
    css_path = "style.css"
    try:
        if os.path.exists(css_path):
            with open(css_path) as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            # Inject data-theme onto <body> so [data-theme="dark"] CSS selectors activate
            theme_attr = theme if theme in ("light", "dark") else "light"
            st.markdown(
                f"<script>document.body.setAttribute('data-theme', '{theme_attr}');</script>",
                unsafe_allow_html=True,
            )
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

    # href is intentionally absent — Streamlit does not handle anchor navigation.
    # Navigation is done via st.switch_page() in render_services() and the sidebar.
    nav_items = [
        {"name": "Home", "active": st.session_state.get("redirect_to", "") == "app.py"},
        {
            "name": "Services",
            "dropdown": [
                {"name": "Diabetes Detection"},
                {"name": "Parkinson's Detection"},
                {"name": "Pneumonia Detection"},
            ],
        },
        {"name": "About", "active": st.session_state.get("redirect_to", "").endswith("about.py")},
        {"name": "Contact", "active": st.session_state.get("redirect_to", "").endswith("contact.py")},
        {"name": "Privacy", "active": st.session_state.get("redirect_to", "").endswith("privacy.py")},
        {"name": "Log in / Sign up", "class": "cta-nav-btn", "active": False},
    ]

    nav_html = "<nav class='nav-menu' role='navigation'>"
    for item in nav_items:
        if "dropdown" in item:
            dropdown_links = "".join(
                f"<span class='dropdown-item'>{sub['name']}</span>"
                for sub in item["dropdown"]
            )
            nav_html += f"""
            <div class='dropdown'>
                <span class='nav-item' aria-haspopup='true'>{item['name']}</span>
                <div class='dropdown-content'>{dropdown_links}</div>
            </div>
            """
        else:
            active_class = "active" if item.get("active", False) else ""
            extra_class = item.get("class", "")
            nav_html += f"<span class='nav-item {extra_class} {active_class}'>{item['name']}</span>"
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
        "<p>" + c['icon'] + " " + (f"<a href='{c['href']}' class='footer-link'>{c['text']}</a>" if 'href' in c else c['text']) + "</p>"
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


def render_services() -> None:
    """Render the three service cards with working Streamlit navigation."""
    SERVICES = [
        {
            "name": "Diabetes Detection",
            "icon": "🩺",
            "model": "XGBoost",
            "accuracy": "88%",
            "desc": "Assess diabetes risk with a high-precision XGBoost model trained on 21 clinical features.",
            "link": "pages/diabetes.py",
        },
        {
            "name": "Parkinson's Disease",
            "icon": "🎙️",
            "model": "Keras DNN",
            "accuracy": "91%",
            "desc": "Detect early Parkinson's signs through voice pattern analysis with a deep neural network.",
            "link": "pages/parkinsons.py",
        },
        {
            "name": "Pneumonia Detection",
            "icon": "🩻",
            "model": "TensorFlow CNN",
            "accuracy": "92%",
            "desc": "Identify pneumonia from chest X-ray images using a convolutional neural network.",
            "link": "pages/pneumonia.py",
        },
    ]

    st.markdown(
        "<h2 class='section-title' style='text-align:center;margin-bottom:2rem'>"
        "Our AI-Powered Health Solutions</h2>",
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for col, svc in zip(cols, SERVICES):
        with col:
            st.markdown(
                f"""
                <div class="service-card">
                    <div class="service-icon">{svc['icon']}</div>
                    <h3>{svc['name']}</h3>
                    <p class="service-meta">{svc['model']} · {svc['accuracy']} accuracy</p>
                    <p>{svc['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.session_state.get("logged_in"):
                if st.button(f"Analyse →", key=f"svc_{svc['link']}", use_container_width=True):
                    st.switch_page(svc["link"])
            else:
                if st.button("Log in to Access", key=f"svc_login_{svc['link']}", use_container_width=True):
                    st.session_state.redirect_to = svc["link"]
                    st.switch_page("pages/login.py")
