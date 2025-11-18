// header.js - Sistema de Header Unificado
function loadHeader() {
    // Verificar se já existe um header para evitar duplicação
    if (document.querySelector('header')) {
        initHeader();
        return;
    }
    
    // Criar elemento header
    const header = document.createElement('header');
    header.innerHTML = `
        <div class="container header-content">
            <a href="#" class="logo">🎄Agendamento+</a>
            <button id="menuBtn" aria-label="Abrir menu">☰</button>
            <nav id="menu" class="nav-links">
                <a href="dashboard.html" class="nav-link">Dashboard</a>
                <a href="serviços.html" class="nav-link">Serviços</a>
                <a href="clientes.html" class="nav-link">Clientes</a>
                 <a href="agendamento.html" class="nav-link">Agendamentos</a>
                <a href="perfil.html" class="nav-link">Perfil</a>
            </nav>
            <button id="themeToggle" class="theme-toggle">Tema Escuro</button>
        </div>
    `;
    
    // Inserir o header no início do body
    document.body.insertBefore(header, document.body.firstChild);
    
    // Inicializar funcionalidades do header
    initHeader();
}

// Inicializar funcionalidades do header
function initHeader() {
    // Elementos do DOM
    const menuBtn = document.getElementById('menuBtn');
    const menu = document.getElementById('menu');
    const themeToggle = document.getElementById('themeToggle');
    
    // =====================
    // CONTROLE DO MENU MOBILE
    // =====================
    if (menuBtn && menu) {
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.toggle('show');
            menuBtn.classList.toggle('active');
            menuBtn.textContent = menu.classList.contains('show') ? '✕' : '☰';
        });
        
        // Fechar menu ao clicar em um link (mobile)
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    menu.classList.remove('show');
                    menuBtn.classList.remove('active');
                    menuBtn.textContent = '☰';
                }
            });
        });
        
        // Fechar menu ao clicar fora
        document.addEventListener('click', (e) => {
            if (!menu.contains(e.target) && !menuBtn.contains(e.target)) {
                menu.classList.remove('show');
                menuBtn.classList.remove('active');
                menuBtn.textContent = '☰';
            }
        });
        
        // Fechar menu ao redimensionar para desktop
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                menu.classList.remove('show');
                menuBtn.classList.remove('active');
                menuBtn.textContent = '☰';
            }
        });
    }
    
    // =====================
    // CONTROLE DO TEMA CLARO/ESCURO
    // =====================
    if (themeToggle) {
        // Verificar tema salvo no localStorage
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeButton(savedTheme);
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeButton(newTheme);
        });
    }
    
    // Marcar link ativo
    highlightActiveLink();
}

// Atualizar texto do botão de tema
function updateThemeButton(theme) {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.textContent = theme === 'light' ? ' Tema Escuro' : ' Tema Claro';
    }
}

// Destacar link ativo na navegação
function highlightActiveLink() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');
        // Remover classe active de todos os links
        link.classList.remove('active');
        
        // Adicionar classe active ao link correspondente à página atual
        if (linkHref === currentPage) {
            link.classList.add('active');
        }
        
        // Tratamento especial para página inicial
        if (currentPage === '' || currentPage === 'index.html') {
            if (linkHref === 'index.html') {
                link.classList.add('active');
            }
        }
    });
}

// Função global para alternar tema
function alternarTema() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeButton(newTheme);
}

// Carregar o header quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', loadHeader);

// Destacar link ativo na navegação
function highlightActiveLink() {
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  const navLinks = document.querySelectorAll('.nav-link');
  
  navLinks.forEach(link => {
    const linkHref = link.getAttribute('href');
    // Remover classe active de todos os links
    link.classList.remove('active');
    
    // Adicionar classe active ao link correspondente à página atual
    if (linkHref === currentPage) {
      link.classList.add('active');
    }
    
    // Tratamento especial para página inicial
    if (currentPage === '' || currentPage === 'index.html') {
      if (linkHref === 'index.html') {
        link.classList.add('active');
      }
    }
  });
}

// Chamar a função quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', highlightActiveLink);
