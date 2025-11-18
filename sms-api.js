// sms-gratuito.js - Sistema de SMS Gratuito com WhatsApp
class SMSWhatsApp {
    constructor() {
        this.configurado = false;
        this.numeroDestino = '';
    }

    configurar(numeroDestino) {
        this.numeroDestino = this.formatarNumero(numeroDestino);
        this.configurado = true;
        localStorage.setItem('whatsapp_numero', this.numeroDestino);
        return true;
    }

    async enviarSMS(destino, mensagem) {
        if (!this.configurado) {
            throw new Error('WhatsApp não configurado');
        }

        const numero = destino || this.numeroDestino;
        const mensagemCodificada = encodeURIComponent(mensagem);
        
        // Abrir WhatsApp Web com mensagem pré-pronta
        const url = `https://web.whatsapp.com/send?phone=${numero}&text=${mensagemCodificada}`;
        
        // Tentar abrir em nova aba
        const novaAba = window.open(url, '_blank');
        
        if (!novaAba) {
            // Fallback: mostrar QR Code para escanear
            this.mostrarQRCode(numero, mensagem);
        }

        return {
            success: true,
            messageId: 'WA_' + Date.now(),
            provider: 'whatsapp_web',
            observacao: 'Mensagem pronta no WhatsApp Web - Envie manualmente',
            url: url
        };
    }

    mostrarQRCode(numero, mensagem) {
        const mensagemCodificada = encodeURIComponent(mensagem);
        const url = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://wa.me/${numero}?text=${mensagemCodificada}`;
        
        const modalHTML = `
            <div class="modal" style="display: flex;">
                <div class="modal-content">
                    <h2>📱 Enviar via WhatsApp</h2>
                    <p>Escaneie o QR Code abaixo com seu celular:</p>
                    <div style="text-align: center; padding: 20px;">
                        <img src="${url}" alt="QR Code WhatsApp" style="border: 2px solid #25D366; border-radius: 10px;">
                    </div>
                    <p><strong>Número:</strong> ${numero}</p>
                    <div class="form-actions">
                        <button onclick="copiarParaAreaTransferencia('${mensagem}')" class="btn btn-primary">
                            <i class="fas fa-copy"></i> Copiar Mensagem
                        </button>
                        <button onclick="fecharModalWhatsApp()" class="btn btn-secondary">
                            <i class="fas fa-times"></i> Fechar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    formatarNumero(numero) {
        return numero.replace(/\D/g, '');
    }
}