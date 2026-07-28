import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Ensure app/ is in sys.path when views are loaded
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.ticket import Ticket
from app.services.database_service import TicketRepository, IntegrationRepository
from app.services.ticket_processor import TicketProcessor
from app.utils.config import load_config, save_config
from app.connectors.factory import ConnectorFactory

processor = TicketProcessor()

def inject_responsive_css():
    """Injects premium, mobile-responsive custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
    /* Styling Streamlit Metrics into beautiful cards */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* Dark Theme compatibility for Metrics */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] {
            background-color: #1e293b;
            border-color: #334155;
            color: #f8fafc;
        }
    }
    
    /* Responsive adjustments for mobile screens */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1.5rem !important;
        }
        
        /* Stack column grids on tablet/mobile if they squish */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 12px;
        }
    }
    
    /* Custom Badge/Status Styling */
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    inject_responsive_css()
    st.header("📈 Helpdesk Overview")
    metrics = TicketRepository.get_dashboard_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Today's Tickets", metrics['todays_tickets'])
    with col2:
        st.metric("Open Tickets", metrics['open_tickets'], delta_color="inverse")
    with col3:
        st.metric("Pending/Resolved", f"{metrics['pending_tickets']} / {metrics['resolved_tickets']}")
    with col4:
        st.metric("Average Confidence", f"{metrics['avg_confidence']:.1f}%")
        
    st.markdown("---")
    
    # Show recent activities
    st.subheader("🔔 Recent Ingested Tickets")
    tickets = TicketRepository.list_tickets(status="All")[:5]
    if tickets:
        for t in tickets:
            with st.expander(f"[{t.ticket_id}] - {t.subject} (From: {t.customer_name}) - Priority: {t.priority}"):
                st.write(f"**Source:** {t.source} | **Category:** {t.category} | **Assigned:** {t.assigned_team}")
                st.write(f"**Description:** {t.body[:200]}...")
    else:
        st.info("No tickets created yet. Use 'Create Ticket' or run the REST API to populate the database.")
        
    st.markdown("---")
    st.subheader("🛠️ Automated Ingestion Channels Showcase")
    st.markdown("Interact with the multi-channel pathways supported by the platform. Click and drag or scroll to rotate the 3D gallery carousel.")
    
    render_circular_gallery_component()

def render_circular_gallery_component():
    import json
    import base64
    import os
    import streamlit.components.v1 as components
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    static_dir = os.path.join(project_root, 'app', 'static', 'gallery')
    
    def get_base64_image(filename):
        path = os.path.join(static_dir, filename)
        if not os.path.exists(path):
            return ""
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
            
    items = [
        {"image": get_base64_image("email_channel.png"), "text": "Email Connector"},
        {"image": get_base64_image("whatsapp_channel.png"), "text": "WhatsApp Link"},
        {"image": get_base64_image("telegram_channel.png"), "text": "Telegram Bot"},
        {"image": get_base64_image("slack_channel.png"), "text": "Slack App"},
        {"image": get_base64_image("web_form_channel.png"), "text": "Web Contact Form"},
        {"image": get_base64_image("api_channel.png"), "text": "REST API FastAPI"}
    ]
    
    bend = 3
    text_color = "#ffffff"
    border_radius = 0.05
    font = "bold 30px Orbitron"
    font_url = "https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap"
    scroll_speed = 2
    scroll_ease = 0.02
    
    html_template = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    html, body {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: transparent;
      user-select: none;
    }
    .circular-gallery {
      width: 100%;
      height: 100%;
      overflow: hidden;
      cursor: grab;
    }
    .circular-gallery:active {
      cursor: grabbing;
    }
    .circular-gallery:focus-visible {
      outline: 2px solid #fff;
      outline-offset: 4px;
    }
  </style>
</head>
<body>
  <div id="gallery-container" class="circular-gallery" tabindex="0" role="region" aria-label="Circular image gallery. Use left and right arrow keys to navigate."></div>

  <script type="module">
    import { Camera, Mesh, Plane, Program, Renderer, Texture, Transform } from 'https://esm.sh/ogl@0.0.32';

    function debounce(func, wait) {
      let timeout;
      return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
      };
    }

    function lerp(p1, p2, t) {
      return p1 + (p2 - p1) * t;
    }

    function autoBind(instance) {
      const proto = Object.getPrototypeOf(instance);
      Object.getOwnPropertyNames(proto).forEach(key => {
        if (key !== 'constructor' && typeof instance[key] === 'function') {
          instance[key] = instance[key].bind(instance);
        }
      });
    }

    const DEFAULT_FONT = 'bold 30px Figtree';
    const DEFAULT_FONT_URL = 'https://fonts.googleapis.com/css2?family=Figtree:wght@400;700&display=swap';

    function deriveFontFamilyFromUrl(url) {
      const fileName = (url.split('/').pop() || 'custom-font').split('?')[0];
      const base = fileName.replace(/\.(woff2?|ttf|otf|eot)$/i, '');
      return base.replace(/[^a-zA-Z0-9-_ ]/g, '').trim() || 'CircularGalleryFont';
    }

    async function loadFontFromStylesheet(url) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Failed to fetch font stylesheet (${response.status})`);
      const cssText = await response.text();
      const faceBlocks = cssText.match(/@font-face\s*{[^}]*}/g) || [];
      let family = null;
      const fontFaces = [];
      for (const block of faceBlocks) {
        const familyMatch = block.match(/font-family:\s*['"]?([^;'"]+)['"]?/);
        const urlMatch = block.match(/url\(\s*['"]?([^'")]+)['"]?\s*\)/);
        if (!familyMatch || !urlMatch) continue;
        family = familyMatch[1].trim();
        const descriptors = {};
        const weightMatch = block.match(/font-weight:\s*([^;]+);/);
        const styleMatch = block.match(/font-style:\s*([^;]+);/);
        const rangeMatch = block.match(/unicode-range:\s*([^;]+);/);
        if (weightMatch) descriptors.weight = weightMatch[1].trim();
        if (styleMatch) descriptors.style = styleMatch[1].trim();
        if (rangeMatch) descriptors.unicodeRange = rangeMatch[1].trim();
        fontFaces.push(new FontFace(family, `url(${urlMatch[1]})`, descriptors));
      }
      if (!family) throw new Error('No @font-face rule found in the stylesheet');
      await Promise.allSettled(
        fontFaces.map(async face => {
          await face.load();
          document.fonts.add(face);
        })
      );
      return family;
    }

    async function loadFontFromFile(url) {
      const family = deriveFontFamilyFromUrl(url);
      const fontFace = new FontFace(family, `url(${url})`);
      await fontFace.load();
      document.fonts.add(fontFace);
      return family;
    }

    async function loadCustomFont(fontUrl) {
      const isStylesheet = fontUrl.includes('fonts.googleapis.com') || /\.css(\?.*)?$/i.test(fontUrl);
      return isStylesheet ? loadFontFromStylesheet(fontUrl) : loadFontFromFile(fontUrl);
    }

    async function resolveFont(font, fontUrl) {
      const effectiveUrl = fontUrl || (font === DEFAULT_FONT ? DEFAULT_FONT_URL : null);
      if (!effectiveUrl) {
        if (document.fonts && document.fonts.load) {
          try {
            await document.fonts.load(font);
            await document.fonts.ready;
          } catch {
            // ignore
          }
        }
        return font;
      }
      try {
        const family = await loadCustomFont(effectiveUrl);
        const sizeMatch = font.match(/^\s*(.*?\d+px)/);
        const prefix = sizeMatch ? sizeMatch[1].trim() : 'bold 30px';
        const resolved = `${prefix} "${family}"`;
        if (document.fonts && document.fonts.load) {
          try {
            await document.fonts.load(resolved);
          } catch {
            // ignore
          }
        }
        return resolved;
      } catch (error) {
        console.error('CircularGallery: unable to load font from', fontUrl, error);
        return font;
      }
    }

    function getFontSize(font) {
      const match = font.match(/(\d+)px/);
      return match ? parseInt(match[1], 10) : 30;
    }

    function createTextTexture(gl, text, font = 'bold 30px monospace', color = 'black') {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      context.font = font;
      const metrics = context.measureText(text);
      const textWidth = Math.ceil(metrics.width);
      const textHeight = Math.ceil(getFontSize(font) * 1.2);
      canvas.width = textWidth + 20;
      canvas.height = textHeight + 20;
      context.font = font;
      context.fillStyle = color;
      context.textBaseline = 'middle';
      context.textAlign = 'center';
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.fillText(text, canvas.width / 2, canvas.height / 2);
      const texture = new Texture(gl, { generateMipmaps: false });
      texture.image = canvas;
      return { texture, width: canvas.width, height: canvas.height };
    }

    class Title {
      constructor({ gl, plane, renderer, text, textColor = '#545050', font = '30px sans-serif' }) {
        autoBind(this);
        this.gl = gl;
        this.plane = plane;
        this.renderer = renderer;
        this.text = text;
        this.textColor = textColor;
        this.font = font;
        this.createMesh();
      }
      createMesh() {
        const { texture, width, height } = createTextTexture(this.gl, this.text, this.font, this.textColor);
        const geometry = new Plane(this.gl);
        const program = new Program(this.gl, {
          vertex: `
            attribute vec3 position;
            attribute vec2 uv;
            uniform mat4 modelViewMatrix;
            uniform mat4 projectionMatrix;
            varying vec2 vUv;
            void main() {
              vUv = uv;
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
          `,
          fragment: `
            precision highp float;
            uniform sampler2D tMap;
            varying vec2 vUv;
            void main() {
              vec4 color = texture2D(tMap, vUv);
              if (color.a < 0.1) discard;
              gl_FragColor = color;
            }
          `,
          uniforms: { tMap: { value: texture } },
          transparent: true
        });
        this.mesh = new Mesh(this.gl, { geometry, program });
        const aspect = width / height;
        const textHeight = this.plane.scale.y * 0.15;
        const textWidth = textHeight * aspect;
        this.mesh.scale.set(textWidth, textHeight, 1);
        this.mesh.position.y = -this.plane.scale.y * 0.5 - textHeight * 0.5 - 0.05;
        this.mesh.setParent(this.plane);
      }
    }

    class Media {
      constructor({
        geometry,
        gl,
        image,
        index,
        length,
        renderer,
        scene,
        screen,
        text,
        viewport,
        bend,
        textColor,
        borderRadius = 0,
        font
      }) {
        this.extra = 0;
        this.geometry = geometry;
        this.gl = gl;
        this.image = image;
        this.index = index;
        this.length = length;
        this.renderer = renderer;
        this.scene = scene;
        this.screen = screen;
        this.text = text;
        this.viewport = viewport;
        this.bend = bend;
        this.textColor = textColor;
        this.borderRadius = borderRadius;
        this.font = font;
        this.createShader();
        this.createMesh();
        this.createTitle();
        this.onResize();
      }
      createShader() {
        const texture = new Texture(this.gl, {
          generateMipmaps: true
        });
        this.program = new Program(this.gl, {
          depthTest: false,
          depthWrite: false,
          vertex: `
            precision highp float;
            attribute vec3 position;
            attribute vec2 uv;
            uniform mat4 modelViewMatrix;
            uniform mat4 projectionMatrix;
            uniform float uTime;
            uniform float uSpeed;
            varying vec2 vUv;
            void main() {
              vUv = uv;
              vec3 p = position;
              p.z = (sin(p.x * 4.0 + uTime) * 1.5 + cos(p.y * 2.0 + uTime) * 1.5) * (0.1 + uSpeed * 0.5);
              gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
            }
          `,
          fragment: `
            precision highp float;
            uniform vec2 uImageSizes;
            uniform vec2 uPlaneSizes;
            uniform sampler2D tMap;
            uniform float uBorderRadius;
            varying vec2 vUv;
            
            float roundedBoxSDF(vec2 p, vec2 b, float r) {
              vec2 d = abs(p) - b;
              return length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0) - r;
            }
            
            void main() {
              vec2 ratio = vec2(
                min((uPlaneSizes.x / uPlaneSizes.y) / (uImageSizes.x / uImageSizes.y), 1.0),
                min((uPlaneSizes.y / uPlaneSizes.x) / (uImageSizes.y / uImageSizes.x), 1.0)
              );
              vec2 uv = vec2(
                vUv.x * ratio.x + (1.0 - ratio.x) * 0.5,
                vUv.y * ratio.y + (1.0 - ratio.y) * 0.5
              );
              vec4 color = texture2D(tMap, uv);
              
              float d = roundedBoxSDF(vUv - 0.5, vec2(0.5 - uBorderRadius), uBorderRadius);
              
              float edgeSmooth = 0.002;
              float alpha = 1.0 - smoothstep(-edgeSmooth, edgeSmooth, d);
              
              gl_FragColor = vec4(color.rgb, alpha);
            }
          `,
          uniforms: {
            tMap: { value: texture },
            uPlaneSizes: { value: [0, 0] },
            uImageSizes: { value: [0, 0] },
            uSpeed: { value: 0 },
            uTime: { value: 100 * Math.random() },
            uBorderRadius: { value: this.borderRadius }
          },
          transparent: true
        });
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.src = this.image;
        img.onload = () => {
          texture.image = img;
          this.program.uniforms.uImageSizes.value = [img.naturalWidth, img.naturalHeight];
        };
      }
      createMesh() {
        this.plane = new Mesh(this.gl, {
          geometry: this.geometry,
          program: this.program
        });
        this.plane.setParent(this.scene);
      }
      createTitle() {
        this.title = new Title({
          gl: this.gl,
          plane: this.plane,
          renderer: this.renderer,
          text: this.text,
          textColor: this.textColor,
          font: this.font
        });
      }
      update(scroll, direction) {
        this.plane.position.x = this.x - scroll.current - this.extra;

        const x = this.plane.position.x;
        const H = this.viewport.width / 2;

        if (this.bend === 0) {
          this.plane.position.y = 0;
          this.plane.rotation.z = 0;
        } else {
          const B_abs = Math.abs(this.bend);
          const R = (H * H + B_abs * B_abs) / (2 * B_abs);
          const effectiveX = Math.min(Math.abs(x), H);

          const arc = R - Math.sqrt(R * R - effectiveX * effectiveX);
          if (this.bend > 0) {
            this.plane.position.y = -arc;
            this.plane.rotation.z = -Math.sign(x) * Math.asin(effectiveX / R);
          } else {
            this.plane.position.y = arc;
            this.plane.rotation.z = Math.sign(x) * Math.asin(effectiveX / R);
          }
        }

        this.speed = scroll.current - scroll.last;
        this.program.uniforms.uTime.value += 0.04;
        this.program.uniforms.uSpeed.value = this.speed;

        const planeOffset = this.plane.scale.x / 2;
        const viewportOffset = this.viewport.width / 2;
        this.isBefore = this.plane.position.x + planeOffset < -viewportOffset;
        this.isAfter = this.plane.position.x - planeOffset > viewportOffset;
        if (direction === 'right' && this.isBefore) {
          this.extra -= this.widthTotal;
          this.isBefore = this.isAfter = false;
        }
        if (direction === 'left' && this.isAfter) {
          this.extra += this.widthTotal;
          this.isBefore = this.isAfter = false;
        }
      }
      onResize({ screen, viewport } = {}) {
        if (screen) this.screen = screen;
        if (viewport) {
          this.viewport = viewport;
          if (this.plane.program.uniforms.uViewportSizes) {
            this.plane.program.uniforms.uViewportSizes.value = [this.viewport.width, this.viewport.height];
          }
        }
        this.scale = this.screen.height / 1500;
        this.plane.scale.y = (this.viewport.height * (900 * this.scale)) / this.screen.height;
        this.plane.scale.x = (this.viewport.width * (700 * this.scale)) / this.screen.width;
        this.plane.program.uniforms.uPlaneSizes.value = [this.plane.scale.x, this.plane.scale.y];
        this.padding = 2;
        this.width = this.plane.scale.x + this.padding;
        this.widthTotal = this.width * this.length;
        this.x = this.width * this.index;
      }
    }

    class App {
      constructor(
        container,
        {
          items,
          bend,
          textColor = '#ffffff',
          borderRadius = 0,
          font = 'bold 30px Figtree',
          scrollSpeed = 2,
          scrollEase = 0.05
        } = {}
      ) {
        document.documentElement.classList.remove('no-js');
        this.container = container;
        this.scrollSpeed = scrollSpeed;
        this.scroll = { ease: scrollEase, current: 0, target: 0, last: 0 };
        this.onCheckDebounce = debounce(this.onCheck, 200);
        this.createRenderer();
        this.createCamera();
        this.createScene();
        this.onResize();
        this.createGeometry();
        this.createMedias(items, bend, textColor, borderRadius, font);
        this.update();
        this.addEventListeners();
      }
      createRenderer() {
        this.renderer = new Renderer({
          alpha: true,
          antialias: true,
          dpr: Math.min(window.devicePixelRatio || 1, 2)
        });
        this.gl = this.renderer.gl;
        this.gl.clearColor(0, 0, 0, 0);
        this.container.appendChild(this.gl.canvas);
      }
      createCamera() {
        this.camera = new Camera(this.gl);
        this.camera.fov = 45;
        this.camera.position.z = 20;
      }
      createScene() {
        this.scene = new Transform();
      }
      createGeometry() {
        this.planeGeometry = new Plane(this.gl, {
          heightSegments: 50,
          widthSegments: 100
        });
      }
      createMedias(items, bend = 1, textColor, borderRadius, font) {
        const galleryItems = items;
        this.mediasImages = galleryItems.concat(galleryItems);
        this.medias = this.mediasImages.map((data, index) => {
          return new Media({
            geometry: this.planeGeometry,
            gl: this.gl,
            image: data.image,
            index,
            length: this.mediasImages.length,
            renderer: this.renderer,
            scene: this.scene,
            screen: this.screen,
            text: data.text,
            viewport: this.viewport,
            bend,
            textColor,
            borderRadius,
            font
          });
        });
      }
      onTouchDown(e) {
        this.isDown = true;
        this.scroll.position = this.scroll.current;
        this.start = e.touches ? e.touches[0].clientX : e.clientX;
      }
      onTouchMove(e) {
        if (!this.isDown) return;
        const x = e.touches ? e.touches[0].clientX : e.clientX;
        const distance = (this.start - x) * (this.scrollSpeed * 0.025);
        this.scroll.target = this.scroll.position + distance;
      }
      onTouchUp() {
        this.isDown = false;
        this.onCheck();
      }
      onWheel(e) {
        const delta = e.deltaY || e.wheelDelta || e.detail;
        this.scroll.target += (delta > 0 ? this.scrollSpeed : -this.scrollSpeed) * 0.2;
        this.onCheckDebounce();
      }
      onKeyDown(e) {
        switch (e.key) {
          case 'ArrowRight':
            e.preventDefault();
            this.scroll.target += this.scrollSpeed * 5;
            this.onCheckDebounce();
            break;
          case 'ArrowLeft':
            e.preventDefault();
            this.scroll.target -= this.scrollSpeed * 5;
            this.onCheckDebounce();
            break;
          case 'Home':
            e.preventDefault();
            this.scroll.target = 0;
            this.onCheckDebounce();
            break;
        }
      }
      onCheck() {
        if (!this.medias || !this.medias[0]) return;
        const width = this.medias[0].width;
        const itemIndex = Math.round(Math.abs(this.scroll.target) / width);
        const item = width * itemIndex;
        this.scroll.target = this.scroll.target < 0 ? -item : item;
      }
      onResize() {
        this.screen = {
          width: this.container.clientWidth,
          height: this.container.clientHeight
        };
        this.renderer.setSize(this.screen.width, this.screen.height);
        this.camera.perspective({
          aspect: this.screen.width / this.screen.height
        });
        const fov = (this.camera.fov * Math.PI) / 180;
        const height = 2 * Math.tan(fov / 2) * this.camera.position.z;
        const width = height * this.camera.aspect;
        this.viewport = { width, height };
        if (this.medias) {
          this.medias.forEach(media => media.onResize({ screen: this.screen, viewport: this.viewport }));
        }
      }
      update() {
        this.scroll.current = lerp(this.scroll.current, this.scroll.target, this.scroll.ease);
        const direction = this.scroll.current > this.scroll.last ? 'right' : 'left';
        if (this.medias) {
          this.medias.forEach(media => media.update(this.scroll, direction));
        }
        this.renderer.render({ scene: this.scene, camera: this.camera });
        this.scroll.last = this.scroll.current;
        this.raf = window.requestAnimationFrame(this.update.bind(this));
      }
      addEventListeners() {
        this.boundOnResize = this.onResize.bind(this);
        this.boundOnWheel = this.onWheel.bind(this);
        this.boundOnTouchDown = this.onTouchDown.bind(this);
        this.boundOnTouchMove = this.onTouchMove.bind(this);
        this.boundOnTouchUp = this.onTouchUp.bind(this);
        this.boundOnKeyDown = this.onKeyDown.bind(this);

        window.addEventListener('resize', this.boundOnResize);
        window.addEventListener('mousewheel', this.boundOnWheel);
        window.addEventListener('wheel', this.boundOnWheel);
        window.addEventListener('mousedown', this.boundOnTouchDown);
        window.addEventListener('mousemove', this.boundOnTouchMove);
        window.addEventListener('mouseup', this.boundOnTouchUp);
        window.addEventListener('touchstart', this.boundOnTouchDown);
        window.addEventListener('touchmove', this.boundOnTouchMove);
        window.addEventListener('touchend', this.boundOnTouchUp);
        this.container?.addEventListener('keydown', this.boundOnKeyDown);
      }
      destroy() {
        window.cancelAnimationFrame(this.raf);
        window.removeEventListener('resize', this.boundOnResize);
        window.removeEventListener('mousewheel', this.boundOnWheel);
        window.removeEventListener('wheel', this.boundOnWheel);
        window.removeEventListener('mousedown', this.boundOnTouchDown);
        window.removeEventListener('mousemove', this.boundOnTouchMove);
        window.removeEventListener('mouseup', this.boundOnTouchUp);
        window.removeEventListener('touchstart', this.boundOnTouchDown);
        window.removeEventListener('touchmove', this.boundOnTouchMove);
        window.removeEventListener('touchend', this.boundOnTouchUp);
        if (this.renderer && this.renderer.gl && this.renderer.gl.canvas.parentNode) {
          this.renderer.gl.canvas.parentNode.removeChild(this.renderer.gl.canvas);
        }
        if (this.container) {
          this.container.removeEventListener('keydown', this.boundOnKeyDown);
        }
      }
    }

    const items = ___ITEMS___;
    const bend = ___BEND___;
    const textColor = "___COLOR___";
    const borderRadius = ___RADIUS___;
    const font = "___FONT___";
    const fontUrl = "___FONT_URL___";
    const scrollSpeed = ___SPEED___;
    const scrollEase = ___EASE___;

    const container = document.getElementById('gallery-container');
    resolveFont(font, fontUrl).then(resolvedFont => {
      const app = new App(container, {
        items,
        bend,
        textColor,
        borderRadius,
        font: resolvedFont,
        scrollSpeed,
        scrollEase
      });
    });
  </script>
</body>
</html>
""".replace("___ITEMS___", json.dumps(items)) \
   .replace("___BEND___", str(bend)) \
   .replace("___COLOR___", text_color) \
   .replace("___RADIUS___", str(border_radius)) \
   .replace("___FONT___", font) \
   .replace("___FONT_URL___", font_url) \
   .replace("___SPEED___", str(scroll_speed)) \
   .replace("___EASE___", str(scroll_ease))
   
    components.html(html_template, height=600)

def render_integrations():
    inject_responsive_css()
    st.header("🔌 Automations & Integration Center")
    st.markdown("Configure external communication channels to automatically ingest support requests. AI validates, parses, translates, and classifies every incoming request in real-time.")
    
    # 1. EMAIL CONNECTOR
    with st.expander("✉️ Email Integration (Gmail, Outlook, Generic IMAP)", expanded=False):
        st.markdown("##### Automatically read support requests from unread emails.")
        
        db_data = IntegrationRepository.get_settings("email")
        enabled = db_data.get("enabled", False)
        cfg = db_data.get("settings", {})
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            email_addr = st.text_input("Email Address", value=cfg.get("email_address", ""), placeholder="support@yourcompany.com")
            app_pw = st.text_input("App Password", value=cfg.get("app_password", ""), type="password", placeholder="Google App Password / SMTP Pass")
            imap_host = st.text_input("IMAP Host", value=cfg.get("imap_host", "imap.gmail.com"), placeholder="imap.gmail.com")
        with col_e2:
            imap_port = st.text_input("IMAP Port", value=str(cfg.get("imap_port", 993)), placeholder="993")
            poll_int = st.number_input("Polling Interval (seconds)", min_value=10, max_value=3600, value=int(cfg.get("polling_interval", 30)), key="email_poll")
            unread_f = st.text_input("Unread Folder", value=cfg.get("unread_folder", "INBOX"))
            processed_f = st.text_input("Processed Folder", value=cfg.get("processed_folder", "Processed"))
            
        is_enabled = st.toggle("Enable Email Connector", value=enabled, key="email_enable_toggle")
        
        col_eb1, col_eb2 = st.columns(2)
        with col_eb1:
            if st.button("Save Email Config", type="primary", key="email_save"):
                new_cfg = {
                    "email_address": email_addr,
                    "app_password": app_pw,
                    "imap_host": imap_host,
                    "imap_port": imap_port,
                    "polling_interval": poll_int,
                    "unread_folder": unread_f,
                    "processed_folder": processed_f
                }
                IntegrationRepository.save_settings("email", is_enabled, new_cfg)
                st.success("Email configuration saved!")
                st.rerun()
        with col_eb2:
            if st.button("Test Email Connection", key="email_test"):
                test_cfg = {
                    "email_address": email_addr,
                    "app_password": app_pw,
                    "imap_host": imap_host,
                    "imap_port": imap_port,
                    "unread_folder": unread_f,
                    "processed_folder": processed_f
                }
                from app.connectors.email_connector import EmailConnector
                connector = EmailConnector(test_cfg)
                with st.spinner("Testing IMAP connection..."):
                    res_status = connector.test_connection()
                if res_status == "Connected":
                    st.success("🟢 Connected successfully!")
                    IntegrationRepository.update_logs("email", connection_status="Connected", add_log_message="Manual connection test successful.")
                elif res_status == "Authentication Failed":
                    st.error("🔴 Authentication Failed: Invalid credentials.")
                    IntegrationRepository.update_logs("email", connection_status="Authentication Failed", add_log_message="Manual connection test: Auth failure.")
                else:
                    st.error("🔴 Disconnected: Check IMAP host/port.")
                    IntegrationRepository.update_logs("email", connection_status="Disconnected", add_log_message="Manual connection test: Connection failure.")
                    
        # Metrics and Logs
        logs_data = IntegrationRepository.get_logs("email")
        st.markdown("---")
        st.markdown("##### Log Status & Metrics")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Connection Status", logs_data.get("connection_status", "Disconnected"))
        col_m2.metric("Last Sync Time", logs_data.get("last_sync", "Never"))
        col_m3.metric("Processed Count", logs_data.get("messages_processed", 0))
        col_m4.metric("Errors Count", logs_data.get("errors", 0))
        st.caption(f"**Last Ingested Ticket ID:** {logs_data.get('last_ticket_created', 'None')}")
        if logs_data.get("logs"):
            st.text_area("Detailed sync log history:", value="\n".join(logs_data.get("logs")), height=150, disabled=True, key="email_log_area")

    # 2. TELEGRAM CONNECTOR
    with st.expander("🤖 Telegram Bot Integration", expanded=False):
        st.markdown("##### Ingest ticket requests sent directly to your Telegram Support Bot.")
        
        db_data = IntegrationRepository.get_settings("telegram")
        enabled = db_data.get("enabled", False)
        cfg = db_data.get("settings", {})
        
        bot_token = st.text_input("Telegram Bot Token", value=cfg.get("bot_token", ""), type="password", placeholder="e.g. 123456:ABC-DEF1234ghIkl-zyx57W2v1u1")
        allowed_chats = st.text_input("Allowed Chat IDs / Usernames (comma-separated)", value=cfg.get("allowed_chats", ""), placeholder="e.g. 987654321, @user1, @group1")
        webhook_url = st.text_input("Webhook URL (If using webhooks instead of polling)", value=cfg.get("webhook_url", ""), placeholder="e.g. https://yourdomain.com/webhook/telegram")
        
        is_enabled = st.toggle("Enable Telegram Bot", value=enabled, key="telegram_enable_toggle")
        
        col_tb1, col_tb2 = st.columns(2)
        with col_tb1:
            if st.button("Save Telegram Config", type="primary", key="telegram_save"):
                new_cfg = {
                    "bot_token": bot_token,
                    "allowed_chats": allowed_chats,
                    "webhook_url": webhook_url
                }
                IntegrationRepository.save_settings("telegram", is_enabled, new_cfg)
                st.success("Telegram configuration saved!")
                st.rerun()
        with col_tb2:
            if st.button("Test Telegram Bot", key="telegram_test"):
                test_cfg = {
                    "bot_token": bot_token,
                    "allowed_chats": allowed_chats,
                    "webhook_url": webhook_url
                }
                from app.connectors.telegram_connector import TelegramConnector
                connector = TelegramConnector(test_cfg)
                with st.spinner("Calling getMe API..."):
                    res_status = connector.test_connection()
                if res_status == "Connected":
                    st.success("🟢 Bot Token is valid! Bot is active.")
                    IntegrationRepository.update_logs("telegram", connection_status="Connected", add_log_message="Manual bot test successful.")
                elif res_status == "Invalid Token":
                    st.error("🔴 Invalid Token: API token rejected.")
                    IntegrationRepository.update_logs("telegram", connection_status="Invalid Token", add_log_message="Manual bot test: Invalid token.")
                else:
                    st.error("🔴 Disconnected: Telegram API unreachable.")
                    IntegrationRepository.update_logs("telegram", connection_status="Disconnected", add_log_message="Manual bot test: Connection failure.")
                    
        logs_data = IntegrationRepository.get_logs("telegram")
        st.markdown("---")
        st.markdown("##### Log Status & Metrics")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Connection Status", logs_data.get("connection_status", "Disconnected"))
        col_m2.metric("Last Sync Time", logs_data.get("last_sync", "Never"))
        col_m3.metric("Processed Count", logs_data.get("messages_processed", 0))
        col_m4.metric("Errors Count", logs_data.get("errors", 0))
        st.caption(f"**Last Ingested Ticket ID:** {logs_data.get('last_ticket_created', 'None')}")
        if logs_data.get("logs"):
            st.text_area("Detailed sync log history:", value="\n".join(logs_data.get("logs")), height=150, disabled=True, key="telegram_log_area")

    # 3. WHATSAPP CONNECTOR
    with st.expander("💬 Meta WhatsApp Cloud API Integration", expanded=False):
        st.markdown("##### Receive customer queries and media automatically from WhatsApp.")
        
        db_data = IntegrationRepository.get_settings("whatsapp")
        enabled = db_data.get("enabled", False)
        cfg = db_data.get("settings", {})
        
        phone_id = st.text_input("Phone Number ID", value=cfg.get("phone_number_id", ""), placeholder="e.g. 109677325203080")
        access_token = st.text_input("Access Token", value=cfg.get("access_token", ""), type="password", placeholder="Meta Permanent Access Token")
        verify_token = st.text_input("Verify Token", value=cfg.get("verify_token", "whatsapp_verify_token"), placeholder="Verify Token for Webhook URL Setup")
        
        st.info("ℹ️ **Webhook Callback URL for Meta Dev Console:** `https://<your-public-url>/webhook/whatsapp`")
        
        is_enabled = st.toggle("Enable WhatsApp Integration", value=enabled, key="whatsapp_enable_toggle")
        
        col_wb1, col_wb2 = st.columns(2)
        with col_wb1:
            if st.button("Save WhatsApp Config", type="primary", key="whatsapp_save"):
                new_cfg = {
                    "phone_number_id": phone_id,
                    "access_token": access_token,
                    "verify_token": verify_token
                }
                IntegrationRepository.save_settings("whatsapp", is_enabled, new_cfg)
                st.success("WhatsApp configuration saved!")
                st.rerun()
        with col_wb2:
            if st.button("Test WhatsApp Connection", key="whatsapp_test"):
                test_cfg = {
                    "phone_number_id": phone_id,
                    "access_token": access_token,
                    "verify_token": verify_token
                }
                from app.connectors.whatsapp_connector import WhatsAppConnector
                connector = WhatsAppConnector(test_cfg)
                with st.spinner("Verifying credentials..."):
                    res_status = connector.test_connection()
                if res_status == "Connected":
                    st.success("🟢 Meta Graph API verified! Connected.")
                    IntegrationRepository.update_logs("whatsapp", connection_status="Connected", add_log_message="Manual connection test successful.")
                elif res_status == "Invalid Token":
                    st.error("🔴 Invalid Token / Phone ID.")
                    IntegrationRepository.update_logs("whatsapp", connection_status="Invalid Token", add_log_message="Manual connection test: Invalid credentials.")
                else:
                    st.error("🔴 Disconnected: Meta Graph API unreachable.")
                    IntegrationRepository.update_logs("whatsapp", connection_status="Disconnected", add_log_message="Manual connection test: API unreachable.")
                    
        logs_data = IntegrationRepository.get_logs("whatsapp")
        st.markdown("---")
        st.markdown("##### Log Status & Metrics")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Connection Status", logs_data.get("connection_status", "Disconnected"))
        col_m2.metric("Last Sync Time", logs_data.get("last_sync", "Never"))
        col_m3.metric("Processed Count", logs_data.get("messages_processed", 0))
        col_m4.metric("Errors Count", logs_data.get("errors", 0))
        st.caption(f"**Last Ingested Ticket ID:** {logs_data.get('last_ticket_created', 'None')}")
        if logs_data.get("logs"):
            st.text_area("Detailed sync log history:", value="\n".join(logs_data.get("logs")), height=150, disabled=True, key="whatsapp_log_area")

    # 4. SLACK CONNECTOR
    with st.expander("🤝 Slack App Integration", expanded=False):
        st.markdown("##### Connect channels or workspaces to ingest ticket submissions.")
        
        db_data = IntegrationRepository.get_settings("slack")
        enabled = db_data.get("enabled", False)
        cfg = db_data.get("settings", {})
        
        bot_token = st.text_input("Bot User OAuth Token", value=cfg.get("bot_token", ""), type="password", placeholder="xoxb-...")
        signing_secret = st.text_input("Signing Secret", value=cfg.get("signing_secret", ""), type="password", placeholder="Slack signing secret")
        app_token = st.text_input("App-Level Token (Optional for Socket Mode)", value=cfg.get("app_token", ""), type="password", placeholder="xapp-...")
        workspace_name = st.text_input("Workspace Name", value=cfg.get("workspace_name", ""), placeholder="e.g. My Workspace")
        allowed_channels = st.text_input("Allowed Channels (comma-separated)", value=cfg.get("allowed_channels", ""), placeholder="e.g. C12345, #support-queue")
        
        st.info("ℹ️ **Webhook Event Subscription Request URL:** `https://<your-public-url>/webhook/slack`")
        
        is_enabled = st.toggle("Enable Slack Integration", value=enabled, key="slack_enable_toggle")
        
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            if st.button("Save Slack Config", type="primary", key="slack_save"):
                new_cfg = {
                    "bot_token": bot_token,
                    "signing_secret": signing_secret,
                    "app_token": app_token,
                    "workspace_name": workspace_name,
                    "allowed_channels": allowed_channels
                }
                IntegrationRepository.save_settings("slack", is_enabled, new_cfg)
                st.success("Slack configuration saved!")
                st.rerun()
        with col_sb2:
            if st.button("Test Slack Connection", key="slack_test"):
                test_cfg = {
                    "bot_token": bot_token,
                    "signing_secret": signing_secret,
                    "app_token": app_token,
                    "workspace_name": workspace_name,
                    "allowed_channels": allowed_channels
                }
                from app.connectors.slack_connector import SlackConnector
                connector = SlackConnector(test_cfg)
                with st.spinner("Testing Slack token..."):
                    res_status = connector.test_connection()
                if res_status == "Connected":
                    st.success("🟢 Slack Token is valid! Bot connected.")
                    IntegrationRepository.update_logs("slack", connection_status="Connected", add_log_message="Manual token verification successful.")
                elif res_status == "Invalid Token":
                    st.error("🔴 Invalid OAuth token.")
                    IntegrationRepository.update_logs("slack", connection_status="Invalid Token", add_log_message="Manual token verification: Invalid token.")
                else:
                    st.error("🔴 Slack API unreachable.")
                    IntegrationRepository.update_logs("slack", connection_status="Disconnected", add_log_message="Manual token verification: Connection failure.")
                    
        logs_data = IntegrationRepository.get_logs("slack")
        st.markdown("---")
        st.markdown("##### Log Status & Metrics")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Connection Status", logs_data.get("connection_status", "Disconnected"))
        col_m2.metric("Last Sync Time", logs_data.get("last_sync", "Never"))
        col_m3.metric("Processed Count", logs_data.get("messages_processed", 0))
        col_m4.metric("Errors Count", logs_data.get("errors", 0))
        st.caption(f"**Last Ingested Ticket ID:** {logs_data.get('last_ticket_created', 'None')}")
        if logs_data.get("logs"):
            st.text_area("Detailed sync log history:", value="\n".join(logs_data.get("logs")), height=150, disabled=True, key="slack_log_area")

    # 5. WEBSITE CONTACT FORM
    with st.expander("🌐 Website Contact Form Integration", expanded=False):
        st.markdown("##### Embed a modern support form directly into your public website.")
        
        db_data = IntegrationRepository.get_settings("website")
        enabled = db_data.get("enabled", False)
        
        is_enabled = st.toggle("Enable Website Form Endpoint", value=enabled, key="website_enable_toggle")
        
        if is_enabled != enabled:
            IntegrationRepository.save_settings("website", is_enabled, {})
            st.success("Website integration status updated!")
            st.rerun()
            
        base_url = st.text_input("Local/Public Server Base URL", value="http://localhost:8000", placeholder="e.g. https://helpdesk.company.com")
        
        from app.connectors.website_connector import WebsiteConnector
        connector = WebsiteConnector()
        widget_code = connector.get_embed_code(base_url)
        
        st.markdown("##### Copy & Paste Embed Script")
        st.markdown("Place this `<script>` block anywhere on your website page to render the contact form widget:")
        st.code(widget_code, language="html")
        
        logs_data = IntegrationRepository.get_logs("website")
        st.markdown("---")
        st.markdown("##### Log Status & Metrics")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Connection Status", logs_data.get("connection_status", "Disconnected"))
        col_m2.metric("Last Sync Time", logs_data.get("last_sync", "Never"))
        col_m3.metric("Processed Count", logs_data.get("messages_processed", 0))
        col_m4.metric("Errors Count", logs_data.get("errors", 0))
        st.caption(f"**Last Ingested Ticket ID:** {logs_data.get('last_ticket_created', 'None')}")
        if logs_data.get("logs"):
            st.text_area("Detailed sync log history:", value="\n".join(logs_data.get("logs")), height=150, disabled=True, key="website_log_area")

    # 6. REST API INTEGRATION
    with st.expander("🚀 REST API Endpoint Integration", expanded=False):
        st.markdown("##### Ingest support tickets directly using REST requests.")
        
        db_data = IntegrationRepository.get_settings("api")
        enabled = db_data.get("enabled", False)
        
        is_enabled = st.toggle("Enable API Ingest Endpoint", value=enabled, key="api_enable_toggle")
        
        if is_enabled != enabled:
            IntegrationRepository.save_settings("api", is_enabled, {})
            st.success("API integration status updated!")
            st.rerun()
            
        st.markdown("##### REST Endpoint Documentation")
        st.markdown("""
        **Endpoint:** `POST /tickets` or `/api/tickets`
        
        **Headers:** `Content-Type: application/json`
        
        **Payload Scheme:**
        ```json
        {
          "customer_name": "Bob Smith",
          "email": "bob@example.com",
          "subject": "Server Downtime Alert",
          "description": "The production DB server timed out on port 5432.",
          "source": "Monitoring System"
        }
        ```
        """)
        
        logs_data = IntegrationRepository.get_logs("api")
        st.markdown("---")
        st.markdown("##### Log Status & Metrics")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Connection Status", logs_data.get("connection_status", "Disconnected"))
        col_m2.metric("Last Sync Time", logs_data.get("last_sync", "Never"))
        col_m3.metric("Processed Count", logs_data.get("messages_processed", 0))
        col_m4.metric("Errors Count", logs_data.get("errors", 0))
        st.caption(f"**Last Ingested Ticket ID:** {logs_data.get('last_ticket_created', 'None')}")
        if logs_data.get("logs"):
            st.text_area("Detailed sync log history:", value="\n".join(logs_data.get("logs")), height=150, disabled=True, key="api_log_area")

    # 7. MANUAL INGESTION (FALLBACK)
    with st.expander("✍️ Manual Ingestion Sandbox (Fallback)", expanded=False):
        st.markdown("##### Manually submit a ticket to test the processing pipeline.")
        
        with st.form("create_ticket_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name", placeholder="E.g. John Doe")
                email = st.text_input("Customer Email", placeholder="E.g. john@example.com")
            with col2:
                source = st.selectbox("Source Channel", ["Manual Entry", "Email", "WhatsApp", "Slack", "Telegram", "REST API"])
                subject = st.text_input("Subject", placeholder="Brief summary of the issue")
                
            body = st.text_area("Ticket Body / Details", placeholder="Enter full details here...")
            uploaded_file = st.file_uploader("Upload Attachment (PDF, Image, Text, Docx, Zip)", type=["pdf", "png", "jpg", "jpeg", "txt", "docx", "zip"])
            
            submitted = st.form_submit_button("Ingest & Process Ticket", type="primary")
            
            if submitted:
                if not customer_name or not email or (not subject and not body):
                    st.error("Please fill in the required fields (Name, Email, and Subject/Body).")
                else:
                    att_name = None
                    att_data = None
                    if uploaded_file is not None:
                        att_name = uploaded_file.name
                        att_data = uploaded_file.read()
                        
                    ticket_id = TicketRepository.get_next_ticket_id()
                    new_ticket = Ticket(
                        ticket_id=ticket_id,
                        customer_name=customer_name,
                        email=email,
                        source=source,
                        subject=subject,
                        body=body,
                        attachment_name=att_name,
                        attachment_data=att_data
                    )
                    
                    with st.spinner("Processing ticket..."):
                        from app.services.ticket_service import TicketService
                        ts_service = TicketService()
                        res = ts_service.process_incoming_ticket(new_ticket)
                        
                    if res.get("status") == "Rejected":
                        st.error(f"Ticket Rejected: {res.get('reason')}")
                    elif res.get("status") == "Spam":
                        st.warning("⚠️ Ticket classified as SPAM and discarded.")
                    else:
                        st.success(f"🎉 Ticket processed successfully! ID: {res.get('ticket_id')}")
                        
                        st.markdown("### Processed Results")
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.info(f"**Category:** {res.get('category')}")
                            st.info(f"**Confidence:** {res.get('confidence'):.1f}%")
                        with col_res2:
                            st.info(f"**Priority:** {res.get('priority')}")
                            st.info(f"**Sentiment:** {res.get('sentiment')}")
                        with col_res3:
                            st.info(f"**Assigned:** {res.get('assigned_team')}")
                            if res.get("is_duplicate"):
                                st.warning(f"⚠️ Duplicate of: {res.get('duplicate_of')}")
                                
                        st.text_area("Generated Auto-Response", value=res.get("auto_response"), height=200, disabled=True, key="manual_res_area")

def render_inbox():
    inject_responsive_css()
    st.header("📥 Helpdesk Inbox")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search = st.text_input("Search", placeholder="ID, name, subject, body...")
    with col2:
        category_filter = st.selectbox("Category Filter", ["All", "Billing", "Technical", "HR", "General", "Needs Human Review"])
    with col3:
        priority_filter = st.selectbox("Priority Filter", ["All", "HIGH", "NORMAL"])
    with col4:
        status_filter = st.selectbox("Status Filter", ["All", "Open", "Pending", "Resolved", "Spam"])
        
    tickets = TicketRepository.list_tickets(search=search, category=category_filter, priority=priority_filter, status=status_filter)
    
    if not tickets:
        st.info("No tickets match the active filters.")
        return
        
    # Convert list of tickets to pandas dataframe for clean rendering
    data = []
    for t in tickets:
        data.append({
            "Source": t.source,
            "Customer": t.customer_name,
            "Category": t.category,
            "Priority": t.priority,
            "Confidence": f"{t.confidence:.1f}%",
            "Status": t.status,
            "Timestamp": t.created_time
        })
    df = pd.DataFrame(data)
    
    # Display table
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Manage/View details
    st.markdown("### 🔍 Ticket Detail Examiner")
    selected_id = st.selectbox("Select Ticket ID to View/Modify", [t.ticket_id for t in tickets])
    
    if selected_id:
        t = TicketRepository.get_ticket(selected_id)
        if t:
            col_det1, col_det2 = st.columns([2, 1])
            with col_det1:
                st.markdown(f"#### **Subject: {t.subject}**")
                st.caption(f"Created: {t.created_time} | Channel: {t.source} | Email: {t.email}")
                st.markdown("**Description:**")
                st.info(t.body)
                
                # Show attachments
                if t.attachment_name:
                    st.markdown(f"📎 **Attachment:** `{t.attachment_name}`")
                    
                # Show entities
                if t.entities:
                    st.markdown("**Extracted Entities:**")
                    ent_cols = st.columns(len(t.entities))
                    for idx, (k, v) in enumerate(t.entities.items()):
                        with ent_cols[idx % len(ent_cols)]:
                            st.metric(k, v)
                            
                # Show merge duplicate option
                if t.merged_with:
                    st.warning(f"⚠️ This ticket has been marked as a possible duplicate of **{t.merged_with}**.")
                    if st.button("Merge and Resolve Ticket", type="secondary"):
                        from app.services.ticket_service import TicketService
                        TicketService().update_status(t.ticket_id, "Resolved")
                        st.success(f"Ticket {t.ticket_id} merged with {t.merged_with} and status set to Resolved.")
                        st.rerun()
            with col_det2:
                st.markdown("#### **Control Center**")
                
                # Status modification
                new_status = st.selectbox("Update Status", ["Open", "Pending", "Resolved", "Spam"], index=["Open", "Pending", "Resolved", "Spam"].index(t.status))
                if new_status != t.status:
                    from app.services.ticket_service import TicketService
                    TicketService().update_status(t.ticket_id, new_status)
                    st.success("Status updated!")
                    st.rerun()
                    
                st.markdown(f"**Classification Confidence:** `{t.confidence:.1f}%`")
                st.markdown(f"**Priority:** `{t.priority}`")
                st.markdown(f"**Sentiment:** `{t.sentiment}`")
                st.markdown(f"**Assigned Department:** `{t.assigned_team}`")
                
                # Activity log
                st.markdown("**History Log:**")
                logs = TicketRepository.get_activity_logs(t.ticket_id)
                for log in logs:
                    st.caption(f"[{log['timestamp']}] {log['action']} - {log['details']}")

def render_predictions():
    inject_responsive_css()
    # Legacy Classifier Sandbox Interface
    st.header("🎯 Sandbox AI Ticket Classifier")
    st.markdown("Test the underlying Scikit-Learn Logistic Regression / Naive Bayes model in sandbox mode.")
    
    # Import legacy predict method to preserve exact logic
    from predict import predict_ticket
    
    subject = st.text_input("Sandbox Subject", placeholder="E.g., Server is down")
    body = st.text_area("Sandbox Body", placeholder="E.g., Production DB connection keeps timing out...")
    
    if st.button("Run Sandbox Prediction", type="primary"):
        if not subject and not body:
            st.warning("Please fill in details.")
        else:
            with st.spinner("Classifying..."):
                res = predict_ticket(subject, body)
                
            col1, col2, col3 = st.columns(3)
            with col1:
                category = res['Predicted Category']
                if category == "Needs Human Review":
                    st.error(f"### ⚠️ {category}")
                else:
                    st.success(f"### 🎯 {category}")
            with col2:
                st.metric("Confidence Score", f"{res['Confidence %']:.2f}%")
            with col3:
                priority = res['Priority']
                if priority == "HIGH":
                    st.error(f"### 🚨 {priority}")
                else:
                    st.info(f"### 🟢 {priority}")
                    
            st.markdown("---")
            st.subheader("Class Probability Visualization")
            prob_df = pd.DataFrame(
                list(res['Probabilities'].items()),
                columns=['Category', 'Probability (%)']
            )
            prob_df.set_index('Category', inplace=True)
            st.bar_chart(prob_df)

def render_analytics():
    inject_responsive_css()
    st.header("📊 Performance & Distribution Analytics")
    
    tickets = TicketRepository.list_tickets(status="All")
    if not tickets:
        st.info("No data available for analytics yet.")
        return
        
    df = pd.DataFrame([{
        "category": t.category,
        "source": t.source,
        "priority": t.priority,
        "sentiment": t.sentiment,
        "status": t.status,
        "confidence": t.confidence,
        "date": t.created_time.split(" ")[0]
    } for t in tickets])
    
    # 2x2 grid of plots
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tickets per Category")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df, x='category', palette='Blues_r', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close()
        
        st.subheader("Tickets per Ingestion Source")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df, x='source', palette='Greens_r', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close()
        
    with col2:
        st.subheader("Sentiment Distribution")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df, x='sentiment', palette='Oranges_r', ax=ax)
        st.pyplot(fig)
        plt.close()
        
        st.subheader("Confidence Score Distribution")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(data=df, x='confidence', kde=True, color='purple', bins=10, ax=ax)
        st.pyplot(fig)
        plt.close()

def render_settings():
    inject_responsive_css()
    st.header("⚙️ Platform Settings")
    config = load_config()
    
    # Routing Rules
    st.subheader("Routing Engine Mappings")
    routing_rules = config.get("routing_rules", {})
    updated_routing = {}
    for cat, team in routing_rules.items():
        updated_routing[cat] = st.text_input(f"Category: {cat} maps to", value=team)
        
    # Thresholds
    st.markdown("---")
    st.subheader("Confidence Threshold")
    confidence_threshold = st.slider("Human Review Fallback Threshold (%)", min_value=0.0, max_value=100.0, value=float(config.get("confidence_threshold", 60.0)))
    
    # Spam words
    st.markdown("---")
    st.subheader("Spam keywords")
    spam_keywords = st.text_area("List keywords (comma-separated)", value=", ".join(config.get("spam_keywords", [])))
    
    # Department contacts
    st.markdown("---")
    st.subheader("🏢 Department Contact Details (Forwarding)")
    st.markdown("Configure email addresses to forward ticket details and copies of customer replies for each department/team.")
    
    contacts = config.get("department_contacts", {})
    updated_contacts = {}
    
    # Get all distinct teams
    teams = list(set(routing_rules.values()))
    for default_team in ["Customer Support (Escalated)", "Spam Folder"]:
        if default_team not in teams:
            teams.append(default_team)
            
    for team in teams:
        updated_contacts[team] = st.text_input(
            f"Forwarding email for '{team}'",
            value=contacts.get(team, "kumaravelu2003@gmail.com")
        )
    
    if st.button("Save Platform Configurations", type="primary"):
        # Compile config
        config["routing_rules"] = updated_routing
        config["confidence_threshold"] = confidence_threshold
        config["spam_keywords"] = [s.strip() for s in spam_keywords.split(",") if s.strip()]
        config["department_contacts"] = updated_contacts
        save_config(config)
        st.success("Configurations saved successfully!")

    st.markdown("---")
    st.subheader("🔄 Database Maintenance")
    st.markdown("Re-run the newly retrained ML classifier on all existing tickets in the database to update their categories, confidence scores, probability predictions, and department assignments.")
    
    if st.button("Re-classify & Route All Existing Tickets", type="secondary"):
        with st.spinner("Re-classifying tickets in database..."):
            from app.services.database_service import TicketRepository
            from app.services.classification_service import ClassificationService
            from app.services.routing_service import RoutingService
            
            tickets = TicketRepository.list_tickets(status="All")
            updated_count = 0
            classifier = ClassificationService()
            
            for t in tickets:
                pred_class, confidence, probs = classifier.predict(t.subject, t.body)
                
                # Check confidence threshold
                threshold = config.get("confidence_threshold", 60.0)
                if confidence < threshold:
                    new_category = "Needs Human Review"
                else:
                    new_category = pred_class
                    
                new_team = RoutingService.get_assigned_team(new_category)
                
                # Only update if they changed
                if t.category != new_category or t.assigned_team != new_team or t.confidence != confidence:
                    t.category = new_category
                    t.confidence = confidence
                    t.assigned_team = new_team
                    TicketRepository.update_ticket(t)
                    TicketRepository.save_prediction(t.ticket_id, new_category, confidence, probs)
                    updated_count += 1
                    
            st.success(f"🎉 Successfully re-classified and updated routing for {updated_count} existing tickets!")
            st.rerun()
