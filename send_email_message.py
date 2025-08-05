"""
Autor: Jardel M. Fialho
Data: 02/03/2025

Descrição: Implementação para envio de emails com mensagens personalizadas e 
assinatura com imagem dado a operação CNC corrente.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import os


def enviar_emails(lista_destinatarios, assunto, mensagem_texto=None, mensagem_html=None, remetente=None,
                  senha=None, servidor_smtp='smtp.gmail.com', porta=587, anexos=None, imagens_inline=None,
                  personalizar_nome=False, assinatura_html=None, imagem_assinatura=None):
    """
    Envia emails personalizados para uma lista de destinatários com opção de assinatura com imagem.

    Args:
        lista_destinatarios (list): Lista de emails ou tuplas (email, nome) se personalizar_nome=True
        assunto (str): Assunto do email
        mensagem_texto (str, opcional): Corpo do email em texto simples
        mensagem_html (str, opcional): Corpo do email em HTML
        remetente (str, opcional): Email do remetente
        senha (str, opcional): Senha ou chave de app do email
        servidor_smtp (str, opcional): Servidor SMTP
        porta (int, opcional): Porta do servidor SMTP
        anexos (list, opcional): Lista de caminhos para arquivos a serem anexados
        imagens_inline (dict, opcional): Dicionário com ID da imagem e caminho do arquivo para o corpo
        personalizar_nome (bool, opcional): Se True, espera tuplas (email, nome) para personalização
        assinatura_html (str, opcional): HTML da assinatura a ser adicionado ao final do email
        imagem_assinatura (str, opcional): Caminho da imagem para a assinatura (referenciada como 'assinatura')

    Returns:
        dict: Resultados do envio {email: sucesso (True/False)}
    """
    try:
        # Obter credenciais
        email_remetente = remetente or os.environ.get('EMAIL_USUARIO')
        email_senha = senha or os.environ.get('EMAIL_SENHA')

        if not email_remetente or not email_senha:
            raise ValueError("Credenciais de email não fornecidas")

        resultados = {}

        # Conectar ao servidor SMTP
        with smtplib.SMTP(servidor_smtp, porta) as server:
            server.starttls()
            server.login(email_remetente, email_senha)

            # Iterar sobre a lista de destinatários
            for dest in lista_destinatarios:
                email_dest = dest if not personalizar_nome else dest[0]
                nome = dest[1] if personalizar_nome and len(dest) > 1 else ""

                try:
                    # Configurar a mensagem
                    msg = MIMEMultipart('alternative')
                    msg['From'] = email_remetente
                    msg['To'] = email_dest
                    msg['Subject'] = assunto

                    # Personalizar mensagem
                    texto_final = mensagem_texto
                    html_final = mensagem_html or ""
                    if personalizar_nome and nome:
                        if texto_final:
                            texto_final = texto_final.replace("{nome}", nome)
                        html_final = html_final.replace("{nome}", nome)

                    # Adicionar corpo em texto simples
                    if texto_final:
                        msg.attach(MIMEText(texto_final, 'plain'))

                    # Adicionar corpo HTML com imagens inline e assinatura
                    if html_final or assinatura_html:
                        msg_related = MIMEMultipart('related')

                        # Combinar mensagem HTML com assinatura
                        html_completo = html_final
                        if assinatura_html:
                            html_completo += "<br><br>" + assinatura_html

                        msg_related.attach(MIMEText(html_completo, 'html'))

                        # Adicionar imagens inline do corpo
                        if imagens_inline:
                            for img_id, img_path in imagens_inline.items():
                                if os.path.isfile(img_path):
                                    with open(img_path, 'rb') as f:
                                        img = MIMEImage(f.read())
                                        img.add_header(
                                            'Content-ID', f'<{img_id}>')
                                        msg_related.attach(img)

                        # Adicionar imagem da assinatura, se fornecida
                        if imagem_assinatura and os.path.isfile(imagem_assinatura):
                            with open(imagem_assinatura, 'rb') as f:
                                img_assinatura = MIMEImage(f.read())
                                img_assinatura.add_header(
                                    'Content-ID', '<assinatura>')
                                msg_related.attach(img_assinatura)

                        msg.attach(msg_related)

                    # Adicionar anexos
                    if anexos:
                        for arquivo in anexos:
                            if os.path.isfile(arquivo):
                                with open(arquivo, 'rb') as f:
                                    attachment = MIMEApplication(f.read())
                                    attachment.add_header('Content-Disposition', 'attachment',
                                                          filename=os.path.basename(arquivo))
                                    msg.attach(attachment)

                    # Enviar o email
                    server.send_message(msg)
                    print(f"Email enviado com sucesso para {email_dest}")
                    resultados[email_dest] = True

                except Exception as e:
                    print(f"Erro ao enviar para {email_dest}: {str(e)}")
                    resultados[email_dest] = False

        return resultados

    except Exception as e:
        print(f"Erro geral ao configurar envio: {str(e)}")
        return {dest[0] if personalizar_nome else dest: False for dest in lista_destinatarios}


# Uso
if __name__ == "__main__":
    remetente = "laac@ufv.br"
    senha = "hiya eehg quqj cptn"

    # Lista de destinatários
    lista_emails = [
        ("jardel.fialho@ufv.br", "Jardel UFV")
    ]

    # Mensagem principal
    main_message = """
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Olá, {nome}!</h2>
            <p>Este é um e-mail de operação do braço robótico do LAAC-UFV.</p>
            <p>Estamos iniciando a captura de imagens. O arquivo "log.txt" em anexo contém os últimos eventos do sistema.</p>
            <p>Atenciosamente,<br>Equipe LAAC-UFV!<br></p>
            <img src="cid:logo" alt="" style="max-width: 300px;">
        </body>
    </html>
    """

    # Assinatura com imagem
    signature = """
    <div style="font-size: 12px; color: #666;">
        <img src="cid:assinatura" alt="Assinatura" style="max-width: 300px;"></p>
    </div>
    """

    imagens = {'logo': 'images/laac.jpg'}
    anexos = ['log.txt']
    signed_image = 'images/logo.png'

    # Enviar emails
    resultados = enviar_emails(
        lista_destinatarios=lista_emails,
        assunto="Captura de imagem iniciada",
        mensagem_html=main_message,
        remetente=remetente,
        senha=senha,
        imagens_inline=None,
        anexos=anexos,
        personalizar_nome=True,
        assinatura_html=signature,
        imagem_assinatura=signed_image
    )

    # Ver resultados
    print("\nResultados do envio:")
    for email, sucesso in resultados.items():
        print(f"{email}: {'Enviado' if sucesso else 'Falhou'}")
