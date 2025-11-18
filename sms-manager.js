// sms-manager.js - Gerenciador de SMS para o Sistema de Agendamentos
class SMSManager {
    constructor() {
        this.smsService = smsService;
        this.config = this.carregarConfiguracao();
        this.notificationInterval = null;
    }

    // Carregar configuração
    carregarConfiguracao() {
        const configSalva = localStorage.getItem('sms_config');
        return configSalva ? JSON.parse(configSalva) : {
            numeroDestino: '',
            intervaloNotificacoes: 60,
            mensagemPersonalizada: '',
            notificacoesAtivas: false,
            horarioInicio: '08:00',
            horarioFim: '20:00'
        };
    }

    // Salvar configuração
    salvarConfiguracao(config) {
        this.config = { ...this.config, ...config };
        localStorage.setItem('sms_config', JSON.stringify(this.config));
    }

    // Gerar mensagem de agendamentos do dia
    gerarMensagemAgendamentos(agendamentos) {
        const hoje = new Date().toISOString().split('T')[0];
        const agendamentosHoje = agendamentos.filter(a => 
            a.data_agendamento === hoje && 
            a.status !== 'cancelado' && 
            a.status !== 'realizado'
        );

        let mensagem = this.config.mensagemPersonalizada ? 
            `${this.config.mensagemPersonalizada}\n\n` : 
            '📅 RESUMO DE AGENDAMENTOS\n\n';

        if (agendamentosHoje.length > 0) {
            mensagem += `Hoje (${this.formatarData(hoje)}) você tem ${agendamentosHoje.length} agendamento(s):\n\n`;
            
            agendamentosHoje.forEach((agendamento, index) => {
                const statusEmoji = this.obterEmojiStatus(agendamento.status);
                mensagem += `${index + 1}. ${agendamento.cliente_nome}\n`;
                mensagem += `   📋 ${agendamento.servico_nome}\n`;
                mensagem += `   ⏰ ${agendamento.hora_agendamento} ${statusEmoji}\n`;
                
                // Adicionar telefone se disponível
                if (agendamento.cliente_telefone) {
                    mensagem += `   📞 ${agendamento.cliente_telefone}\n`;
                }
                
                mensagem += '\n';
            });

            // Adicionar próximos agendamentos (próximos 2 dias)
            const amanha = new Date();
            amanha.setDate(amanha.getDate() + 1);
            const amanhaStr = amanha.toISOString().split('T')[0];

            const depoisAmanha = new Date();
            depoisAmanha.setDate(depoisAmanha.getDate() + 2);
            const depoisAmanhaStr = depoisAmanha.toISOString().split('T')[0];

            const agendamentosFuturos = agendamentos.filter(a => 
                (a.data_agendamento === amanhaStr || a.data_agendamento === depoisAmanhaStr) && 
                a.status !== 'cancelado'
            ).slice(0, 3); // Limitar a 3 agendamentos

            if (agendamentosFuturos.length > 0) {
                mensagem += `🔮 PRÓXIMOS AGENDAMENTOS:\n\n`;
                agendamentosFuturos.forEach(agendamento => {
                    mensagem += `• ${this.formatarData(agendamento.data_agendamento)} - ${agendamento.hora_agendamento}\n`;
                    mensagem += `  ${agendamento.cliente_nome} - ${agendamento.servico_nome}\n\n`;
                });
            }
        } else {
            mensagem += `📅 AGENDAMENTOS DE HOJE (${this.formatarData(hoje)})\n\n`;
            mensagem += `Não há agendamentos para hoje. 🎉\n\n`;
            mensagem += `Aproveite para organizar sua agenda!`;
        }

        // Adicionar rodapé
        mensagem += `\n\n---\nAgendamento+ • ${new Date().getFullYear()}`;

        return mensagem;
    }

    // Gerar mensagem de lembrete individual
    gerarMensagemLembrete(agendamento, minutosRestantes) {
        const statusEmoji = this.obterEmojiStatus(agendamento.status);
        
        let mensagem = `🔔 LEMBRETE DE AGENDAMENTO\n\n`;
        mensagem += `Cliente: ${agendamento.cliente_nome}\n`;
        mensagem += `Serviço: ${agendamento.servico_nome}\n`;
        mensagem += `Horário: ${agendamento.hora_agendamento}\n`;
        mensagem += `Status: ${agendamento.status} ${statusEmoji}\n`;
        
        if (minutosRestantes <= 30) {
            mensagem += `\n⏰ ATENÇÃO: O agendamento começa em ${minutosRestantes} minutos!\n`;
        } else {
            mensagem += `\nℹ️  O agendamento está programado para daqui a ${minutosRestantes} minutos.\n`;
        }

        if (agendamento.cliente_telefone) {
            mensagem += `\n📞 Contato: ${agendamento.cliente_telefone}`;
        }

        mensagem += `\n\n---\nAgendamento+ • ${new Date().getFullYear()}`;

        return mensagem;
    }

    // Enviar SMS de agendamentos
    async enviarSMSAgendamentos(agendamentos, destinatario = null) {
        if (!this.smsService.verificarConfiguracao()) {
            throw new Error('Serviço SMS não configurado');
        }

        const destino = destinatario || this.config.numeroDestino;
        if (!destino) {
            throw new Error('Nenhum destinatário configurado');
        }

        const mensagem = this.gerarMensagemAgendamentos(agendamentos);
        return await this.smsService.enviarSMS(destino, mensagem);
    }

    // Enviar lembrete individual
    async enviarLembrete(agendamento, minutosRestantes, destinatario = null) {
        if (!this.smsService.verificarConfiguracao()) {
            throw new Error('Serviço SMS não configurado');
        }

        const destino = destinatario || this.config.numeroDestino;
        if (!destino) {
            throw new Error('Nenhum destinatário configurado');
        }

        const mensagem = this.gerarMensagemLembrete(agendamento, minutosRestantes);
        return await this.smsService.enviarSMS(destino, mensagem);
    }

    // Iniciar sistema de notificações automáticas
    iniciarNotificacoesAutomaticas(agendamentosCallback) {
        this.pararNotificacoes();

        if (!this.config.notificacoesAtivas || !this.config.numeroDestino) {
            console.log('Notificações automáticas desativadas');
            return;
        }

        const intervaloMs = this.config.intervaloNotificacoes * 60 * 1000;
        
        this.notificationInterval = setInterval(() => {
            this.verificarAgendamentosProximos(agendamentosCallback);
        }, intervaloMs);

        // Verificar imediatamente
        this.verificarAgendamentosProximos(agendamentosCallback);

        console.log(`Sistema de notificações iniciado - Verificando a cada ${this.config.intervaloNotificacoes} minutos`);
    }

    // Parar notificações automáticas
    pararNotificacoes() {
        if (this.notificationInterval) {
            clearInterval(this.notificationInterval);
            this.notificationInterval = null;
            console.log('Sistema de notificações parado');
        }
    }

    // Verificar agendamentos próximos
    async verificarAgendamentosProximos(agendamentosCallback) {
        if (!this.dentroDoHorarioComercial()) {
            return;
        }

        try {
            const agendamentos = await agendamentosCallback();
            const agora = new Date();
            const hoje = agora.toISOString().split('T')[0];

            const agendamentosProximos = agendamentos.filter(a => {
                if (a.data_agendamento !== hoje || 
                    a.status === 'cancelado' || 
                    a.status === 'realizado') {
                    return false;
                }

                const horaAgendamento = new Date(`${a.data_agendamento}T${a.hora_agendamento}`);
                const diferencaMinutos = (horaAgendamento - agora) / (1000 * 60);
                
                // Notificar se está entre 5 e 60 minutos
                return diferencaMinutos > 0 && diferencaMinutos <= 60;
            });

            for (const agendamento of agendamentosProximos) {
                const horaAgendamento = new Date(`${agendamento.data_agendamento}T${agendamento.hora_agendamento}`);
                const diferencaMinutos = Math.round((horaAgendamento - agora) / (1000 * 60));

                // Verificar se já foi notificado recentemente
                const notificadoRecentemente = this.verificarNotificacaoRecente(agendamento.id);
                if (!notificadoRecentemente) {
                    await this.enviarLembrete(agendamento, diferencaMinutos);
                    this.registrarNotificacao(agendamento.id);
                    
                    console.log(`Lembrete enviado: ${agendamento.cliente_nome} em ${diferencaMinutos} minutos`);
                }
            }
        } catch (error) {
            console.error('Erro ao verificar agendamentos próximos:', error);
        }
    }

    // Verificar se está dentro do horário comercial
    dentroDoHorarioComercial() {
        const agora = new Date();
        const horas = agora.getHours();
        const minutos = agora.getMinutes();
        const horaAtual = horas + minutos / 60;

        const [inicioHora, inicioMinuto] = this.config.horarioInicio.split(':').map(Number);
        const [fimHora, fimMinuto] = this.config.horarioFim.split(':').map(Number);

        const horaInicio = inicioHora + inicioMinuto / 60;
        const horaFim = fimHora + fimMinuto / 60;

        return horaAtual >= horaInicio && horaAtual <= horaFim;
    }

    // Verificar se já foi notificado recentemente (evitar spam)
    verificarNotificacaoRecente(agendamentoId) {
        const notificacoes = JSON.parse(localStorage.getItem('sms_notificacoes') || '{}');
        const ultimaNotificacao = notificacoes[agendamentoId];
        
        if (!ultimaNotificacao) return false;

        const tempoDesdeUltimaNotificacao = Date.now() - ultimaNotificacao;
        return tempoDesdeUltimaNotificacao < 30 * 60 * 1000; // 30 minutos
    }

    // Registrar notificação
    registrarNotificacao(agendamentoId) {
        const notificacoes = JSON.parse(localStorage.getItem('sms_notificacoes') || '{}');
        notificacoes[agendamentoId] = Date.now();
        localStorage.setItem('sms_notificacoes', JSON.stringify(notificacoes));
    }

    // Utilitários
    formatarData(data) {
        const [ano, mes, dia] = data.split('-');
        return `${dia}/${mes}/${ano}`;
    }

    obterEmojiStatus(status) {
        const emojis = {
            'pendente': '⏳',
            'confirmado': '✅',
            'realizado': '🎉',
            'cancelado': '❌'
        };
        return emojis[status] || '📝';
    }

    // Obter relatório completo
    obterRelatorioCompleto() {
        const estatisticasSMS = this.smsService.obterEstatisticas();
        const historico = this.smsService.obterHistorico().slice(0, 10); // Últimos 10

        return {
            configuracao: this.config,
            estatisticas: estatisticasSMS,
            historicoRecente: historico,
            servicoAtivo: this.smsService.verificarConfiguracao(),
            notificacoesAtivas: this.config.notificacoesAtivas && this.notificationInterval !== null
        };
    }
}

// Instância global do gerenciador SMS
const smsManager = new SMSManager();