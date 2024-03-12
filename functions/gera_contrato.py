from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
import psycopg2 as pg 
import num2words
from datetime import datetime

def data(mes):
    meses = ['01','02','03','04','05','06','07','08','09','10','11','12']
    nome_mes = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
    
    for x in range(len(meses)):
        if mes == meses[x]:
            return nome_mes[x]


def gera_contrato(caminho,seq_contrato,conexao):
    cursor = conexao.cursor()
    
    cnv = canvas.Canvas(f"{caminho}")
    
        
    def cria_quadrado(seq_contrato):
        altura = -20

        # Retangulo
        cnv.rect(35,330,500,altura)

        # Linhas

        cnv.setFontSize(12)
        posicao = 315
        cnv.drawString(125,posicao,"Produto")

        cnv.line(250,330,250,310)

        cnv.drawString(270,posicao,"Quantidade")

        cnv.line(350,330,350,310)

        cnv.drawString(365,posicao,"Unitario")

        cnv.line(450,330,450,310)

        cnv.drawString(475,posicao,"Total")


        cursor.execute(f'''
                select 
                ek_contrato_detalhe.seq_contrato_detalhe,
                ek_contrato_detalhe.seq_contrato,
                ek_contrato_detalhe.cod_produto,
                ek_contrato_detalhe.desc_item_contrato,
                ek_contrato_detalhe.vl_item_contrato,
                ek_contrato_detalhe.quantidade,
                ek_contrato.franquia,
                ek_contrato_detalhe.unid_medida
                from ek_contrato_detalhe inner join ek_contrato on ek_contrato_detalhe.seq_contrato = ek_contrato.seq_contrato
                where ek_contrato.seq_contrato = {seq_contrato} 
                        ''')
        resultado = cursor.fetchall()
        
        cursor.execute(f'select franquia from ek_contrato where seq_contrato = {seq_contrato}')
        franquia = cursor.fetchall()[0][0]
        
        
        
        inicio_linha = 310
        soma_produtos = 0

        for x in resultado:
            
            texto_franquia = ''
            if franquia == 1:
                if x[5] > 1:
                    texto_franquia = 'Dias'
                else:
                    texto_franquia = 'Dia'
            elif franquia == 7:
                if x[5] > 1:
                    texto_franquia = 'Semanas'
                else:
                    texto_franquia = 'Semana'
            elif franquia == 15:
                if x[5] > 1:
                    texto_franquia = 'Quinzenas'
                else :
                    texto_franquia = 'Quinzena'
            elif franquia == 30:
                if x[5] > 1:
                    texto_franquia = 'Meses'
                else:
                    texto_franquia = 'Mês'
            
            cnv.setFontSize(8)
            posicao -= 22
            cnv.drawString(37,posicao,str(x[3])[:39])
            cnv.drawString(270,posicao,f"1 UN / {x[5]} {x[7]}")
            cnv.drawString(360,posicao,str(f'R$ {x[4]:.2f}')) 
            cnv.drawString(460,posicao,f"R$ {(x[5]) * (x[4]):.2f}")
            soma_produtos += float(x[5]) * float(x[4])
            
            inicio_linha -= 22
            cnv.line(35,inicio_linha,535,inicio_linha)
            
        #inicio_linha -= 22 * len(resultado)
        cnv.line(35,310,35,inicio_linha)
        cnv.line(535,310,535,inicio_linha)
        cnv.line(35,inicio_linha,535,inicio_linha)
            
        cnv.line(250,310,250,inicio_linha)
        cnv.line(350,310,350,inicio_linha)
        cnv.line(450,310,450,inicio_linha)


        cnv.line(450,inicio_linha,450,inicio_linha -20)
        cnv.line(535,inicio_linha,535,inicio_linha -20)
        cnv.line(450,inicio_linha -20 ,535,inicio_linha - 20)

        #cnv.drawString(460,inicio_linha - 15,f"R$ {round(float(soma_produtos),2)}")
        cnv.drawString(460,inicio_linha - 15,f"R$ {soma_produtos:.2f}")
        return f'{soma_produtos:.2f}'
    
    
    def gera_contrato_sub(seq_contrato):
    

        cursor.execute(
            f'''
                select nome,
                    (case when cpf is null then cnpj
	else cpf
	end) as "Documento",
	(case when endereco is null then 'VAZIO'
	else endereco
	end)
	"endereco",
	
	(case when compl_endereco is null then ''
	else compl_endereco
	end) as "complemento",
	
	(case when num_endereco is null then 'SN'
	else 'N° ' || num_endereco end) as "Numero endereco",
	
	(case when ek_pessoa.bairro is null then 'VAZIO'
	else ek_pessoa.bairro
	end) as "Bairro",

	(case when ek_cidade.nome_cidade is null then 'VAZIO'
	else ek_cidade.nome_cidade || '-' ||ek_estado.sigla_estado 
	end) as "cidade",
		
	(case when ek_pessoa.cep is null then 'VAZIO'
		else ek_pessoa.cep
		end) as "cep"
                from ek_pessoa left join ek_cidade on ek_cidade.num_cidade = ek_pessoa.cidade
                left join ek_estado on ek_estado.num_estado = ek_pessoa.estado
                where cod_pessoa in (
                                        select cod_pessoa from ek_contrato where seq_contrato = {seq_contrato}
                                    )

            '''
        )
        
        cliente = cursor.fetchall()[0]
        
        cursor.execute(f'''
                        select 
                        ek_empresa.nome_empresa,
                        ek_empresa.cnpj,
                        ek_empresa.endereco,
                        ek_empresa.numero,
                        ek_empresa.bairro,
                        ek_empresa.cep
                        from ek_empresa where num_empresa in 
                        (select num_empresa from ek_contrato where seq_contrato = {seq_contrato})
                       ''')
        dadosEmpresa = cursor.fetchall()[0]
        cnpj_empresa = dadosEmpresa[1][:2] + '.' + dadosEmpresa[1][2:5] + '.' + dadosEmpresa[1][5:8] + '/' + dadosEmpresa[1][8:12] + '-' + dadosEmpresa[1][12:]
        cep_empresa = dadosEmpresa[5][:2] + '.' + dadosEmpresa[5][2:5] + '-' + dadosEmpresa[5][5:]
        
        cursor.execute(
            f'''
                select * from ek_contrato 
                where seq_contrato = {seq_contrato}
            '''
        )
        contrato = cursor.fetchall()[0]
        
    
        
        cnv.setTitle(f'Contrato {contrato[0]}')


        cnv.drawImage("C:/ekoos_contratos_api/functions/cabeçalho.jpeg",30,730,width=550)


        cnv.setFontSize(15)
        cnv.drawCentredString(300,715,'PROPOSTA COMERCIAL')
        cnv.drawCentredString(300,690,'CONTRATO DE LOCAÇÃO DE GRUPO GERADOR')


        cursor.execute(f'''
                            select desc_item_contrato 
                            from ek_contrato_detalhe 
                            where seq_contrato = {seq_contrato}''')
        descricao = cursor.fetchall()

        lista_produtos = []

        for item in descricao:
            lista_produtos.append(f"{item[0]}<br/>")
            
        
        documento = str(cliente[1])
        cep = str(cliente[7])
        cep = f'CEP {cep[:2]}.{cep[2:5]}-{cep[5:]}' if cep != 'VAZIO' else cep
        
        if len(documento) == 14:
            documento = f'CNPJ: {documento[0:2]}.{documento[2:5]}.{documento[5:8]}/{documento[8:12]}-{documento[12:]}'
        elif len(documento) == '11':
            documento = f'CPF: {documento[0:3]}.{documento[3:6]}.{documento[6:9]}-{documento[9:]}'
        
        
        p = Paragraph(
            f'''
            1.	<b>Contratante:</b><br /><br />
            {cliente[0].strip()}, {documento}, ENDEREÇO: {cliente[2].strip() + ' ' + str(cliente[3]) + ' ' + str(cliente[4].strip()) }, {cliente[5].strip()}, {cliente[6]},{cep}, denomidade Locatária.<br /><br /><br />
            2.	<b>Contratado:</b><br /><br />
            {dadosEmpresa[0]}, CNPJ {cnpj_empresa}, ENDEREÇO: {dadosEmpresa[2]}, {dadosEmpresa[3]}, {dadosEmpresa[4]}, LUIS EDUARDO MAGALHÃES - BA, CEP {cep_empresa}. Denominada locadora.<br /><br />
            3.	<b>Objeto:</b><br /><br />
            {''.join(lista_produtos)}'''
        )
        p.wrapOn(cnv,500,25)
        p.drawOn(cnv,35,400)
        
        numero = cria_quadrado(seq_contrato=seq_contrato)
        
        p = Paragraph(f'''4.<b>Valores:</b><br/>Propomos locar os equipamentos solicitados pelo valor total de R$ {str(numero).replace('.',',')} ({num2words.num2words(numero,lang='pt-br')} reais) referente a: <br /><br />''')
        p.wrapOn(cnv,500,25)
        p.drawOn(cnv,35,330)


        #inicio_linha -= 50

        if len(lista_produtos) < 9:
            cnv.drawImage(R"C:/ekoos_contratos_api/functions/footer.jpeg",10,0)

        cnv.showPage()


    
        cnv.drawImage("C:/ekoos_contratos_api/functions/cabeçalho.jpeg",30,710,width=550)
        
        condicoes = [11,13,14,15,16,17,18]
        descricao_condicao = ['combustível','cabos','chave transferência manual','chave transferência automática','transporte','instalação','manutenção']
        possui_condicao = ''
        nao_possui_condicao = ''
        
        for x in range(len(condicoes)):
            if contrato[condicoes[x]] == 'S':
                possui_condicao += f'{descricao_condicao[x]},'
            else:
                nao_possui_condicao += f'{descricao_condicao[x]},'
            
        p = Paragraph(
            f'''
        <b> Observações:</b><br/><br/>
        Em caso de não conter nessa proposta serviço(s) extra ou acessório(s) como: cabo(s), chave de transferência automático (QTAs), Operador, Transporte de Equipamento(s) com sua(s) devida(s) especificação(ões) de quantidade e potência, solicitar com antecedência pois está sujeito a atrasos na entrega do(s) equipamento(s).<br/><br/>
        A preparação e mobilização do(s) equipamento(s) ocorrerá após a assinatura deste documento, sendo assim a não assinatura do mesmo a H BRASIL LTDA não irá disponibilizar quaisquer equipamentos para os fins prepostos da locação.<br/><br/>

        5.	<b>Condições de Fornecimento:</b><br/><br/>
        5.1.	Entende-se que a diária no período contratado é de {contrato[21]} horas por dia, devendo o excedente deste limite de horas ser pago adicionalmente, ao mesmo preço da hora normal contratada. Na situação da hora contratada estiver com valor 0 (zero), entende-se automaticamente que o(s) equipamento(s) está sendo disponibilizado para funcionamento em regime de standby ou backup.<br/><br/>
        5.2.	Entende-se entre as partes desta proposta que está incluso no valor total geral: locação do equipamento,{possui_condicao[:-1]}.<br/><br/>
        5.3.	Entende-se entre as partes desta proposta que está excluso no valor total: {nao_possui_condicao[:-1]}.<br/><br/>
        5.4.	É de responsabilidade da locadora, por si ou por terceiros credenciados, em ambos as hipóteses sem qualquer ônus para a locatária, os serviços técnicos, manutenção e reparo do equipamento, substituindo, também por sua conta todas as peças que se fizeram necessário em decorrência do uso normal. Esses serviços serão prestados exclusivamente no território nacional e durante o horário normal de expediente comercial da Locadora. Se necessário que estes serviços sejam prestados fora desse horário normal a pedido da locatária, as despesas de atendimento extraordinário serão cobradas. Nas localidades de difícil acesso, onde não haja condições de atendimento ‘in loco’ pela locadora ou por terceiros credenciados, a assistência será prestada em local previamente acordado entre as partes, correndo os gastos referente ao transporte do equipamento por conta da Locatária.<br/><br/>
        5.5.	Será de exclusiva responsabilidade da locatária todos os danos e avarias causadas aos, que, comprovadamente, possam ser atribuídas à culpa exclusiva a este ou a seus funcionários, preposto e/ou prestadores de serviços.<br/><br/>
        5.6.	Em caso de sinistro no(s) equipamento(s), será exigido a presença de um preposto da locatária para devolução do(s) mesmo(s), será cobrado normalmente a locação até que se pague o valor indenizatório, para a recuperação do(s) equipamento(s).<br/><br/>
        5.7.	Os valores contidos nesta proposta são para o mínimo de 1 mês corridos(s), quando a locatária, deverá devolver o(s) bem(ns) locado(s), ou renovável por período igual.<br/><br/>
        5.8.	A ELETROMECANICA BRASIL LEM LTDA garante disponibilidade do(s) equipamento(s) para o período desejado, desde que confirmado com antecedência.
            '''
        )

        p.wrapOn(cnv,500,25)
        p.drawOn(cnv,35,150)


        cnv.drawImage(R"C:/ekoos_contratos_api/functions/footer.jpeg",10,0)


        cnv.showPage()

    
        cnv.drawImage("C:/ekoos_contratos_api/functions/cabeçalho.jpeg",30,710,width=550)

        datainicial = str(contrato[5])
        datafinal = str(contrato[6])
        p = Paragraph(
            f'''
            5.9.	A locatária deverá fornecer os dados cadastrais atualizados onde o mesmo estará sujeito a aprovação após as devidas consultas. Como também os contatos para envio dos BMs (boletins de medição), faturas de locação, boletos e notas fiscais, responsáveis por recebimento de equipamento(s) e desmobilização do(s) mesmo(s).<br/><br/>
        5.10.	A locatária deverá disponibilizar o(s) equipamento(s) em perfeita condição de uso, dentro do prazo e condições contratados.<br/><br/>
        5.11.	É de suma importância o locatário repassar a informação de tensão em que o grupo gerador deve ser disponibilizado. É obrigação do locatário conferir a tensão do gerador antes de interligar a sua rede elétrica, com objetivo de evitar danos a equipamentos por tensão diferente da solicitada.<br/><br/>
        5.12.	O locatário tem ciência que os equipamentos contidos nesse contrato que venham utilizar bandeja de contenção a Locadora (ELETROMECANICA BRASIL LEM LTDA) não se responsabilizam-se pela drenagem e dispensa de resíduos que seja água, combustível, óleo lubrificante ou qualquer outro que venha estar no interior da bandeja de contenção, onde é de exclusiva responsabilidade do locatário em manter o acessório com o mínimo possível de resíduos para que não venha danificar o patrimônio locado. Assim desta maneira entende-se qualquer dano que o patrimônio locado sofra.<br/><br/><br/>
        6.	<b>Locatária tem Ciência</b><br/><br/>

        6.1.	A locatária está de acordo com as cláusulas para cobrança:<br/><br/>
        6.1.1.	Para o período inicial de locação de {datainicial[8:10] + '/' + datainicial[5:7] +'/' + datainicial[0:4]} à {datafinal[8:10] + '/' + datafinal[5:7] +'/' + datafinal[0:4]}. A locatária terá 15 dias para o pagamento da fatura de locação via transferencia bancária. Em caso de renovação de locação serão emitidos a fatura e boleto seguindo o mesmo procedimento anterior onde será considerado o inicio da cobrança o primeiro dia após o período anterior faturado.<br/><br/>
        6.1.2.	Em caso da locação para eventos a locatária deverá realizar o pagamento a vista antecipado para validação de aceito do atendimento para esta proposta, caso seja negociado com o representante da locadora (Hugo Brasil Matos) alguma outra forma de pagamento além da descrita nessa clausula, deverá ser comunicado via e-mail e encaminhar junto o comprovante de pagamento. Além de estar sujeito a não fornecimento do atendimento.<br/><br/>
        6.1.3.	Será emitido a locatária, boletim de medição (BM), após o último dia do período de locação anterior faturado com as seguintes informações de horas trabalhadas do equipamento. A locatária devera analisar o BM, manifestando-se em posição de aprovação ou negação referente a medição dentro do prazo de 5 (cinco) dias, contado a partir do recebimento do BM, sob pena de se configurar autorização tácita para faturamento, ficando desde já estabelecido que eventuais divergências serão corrigidas no próximo período de faturamento. <br/><br/>
        6.1.4.	Em caso de excesso de horas além do contratado referente ao equipamento será emitido fatura de locação e boleto para cobrança referente as horas adicionais, fica explicito que a data inicial do faturamento de horas excedentes e emissão do boleto bancário é a data de emissão do BM, com prazo de vencimento de 10 (dez) dias.<br/><br/>
        6.1.5.	Em caso que for contratado os serviços como manutenção, assistência técnica, mobilização/demobilização de equipamentos e demais serviços a locadora, será destacado separadamente da locação, onde será enviado a cobrança a locatária após a conclusão do serviço com prazo para pagamento de 10(dez) dias, contados a partir da data de realização do serviço.<br/><br/>
            '''
        )

        p.wrapOn(cnv,500,25)
        p.drawOn(cnv,35,80)

        cnv.drawImage(R"C:/ekoos_contratos_api/functions/footer.jpeg",10,0)

        cnv.showPage()


    
        cnv.drawImage("C:/ekoos_contratos_api/functions/cabeçalho.jpeg",30,710,width=550)

        p = Paragraph(
            '''6.2.	A locadora suspenderá quaisquer assistência técnica rente a locatária referente ao item locado ao poder da mesma, quando houver fatura em atraso, sem desconto referente aos dias de não funcionamento do equipamento locado.<br/><br/>
        6.3.	Fica desde já estabelecido, que em caso de atraso no pagamento de alugueis, acessórios e encargos da locação, a locatária e seus fiadores, poderão ser, se assim desejar a locadora ou seu procurador, incluídos na lista de restrições comerciais do SPC (serviço de proteção do consumidor) e SERASA, após notificação ou aviso através de E-MAIL ou outra via formal de aviso.<br/><br/>
        6.4.	No caso da locatária, não efetuar o pagamento na data do vencimento, estará obrigada a pagar com correção de 4% (quatro porcento) ao mês, até a data do efetivo pagamento, além de outras despesas cartoriais e honorários advocatícios, se necessário.<br/><br/>
        6.5.	A locatária responsabiliza-se por manter sempre atualizado o cadastro rente a locadora, inclusive em relação ao e-mail para recebimento das notas, da fatura e BMs.<br/><br/>
        6.6.	Confiar de preferencia a locadora todo e qualquer serviço de reparo e assistência técnica ao objeto do presente contrato.<br/><br/>
        6.7.	Permitir o acesso de pessoal autorizado da locadora para realização da manutenção ou reparos de equipamento e, ainda, para o seu desligamento ou remoção, nas hipóteses cabíveis.<br/><br/>
        6.8.	A locadora não poderá, sem a previa e expressa anuência da locadora, alienar, ceder, sublocar ou ainda dar em comodato os equipamentos locados ou os direitos decorrentes do presente contrato, nem de qualquer forma permitir que tais equipamentos entrem na posse de terceiros.<br/><br/>6.9.	A locadora por sua vez, poderá, a qualquer tempo, transferir ou ceder os direitos, títulos ou interesses que possa ter em decorrência deste contrato, mediante previa e expressa autorização do locatário.<br/><br/>
        6.10.	A locatária obriga-se a devolver o bem locado na mesma condição de conservação e funcionamento que declara ter recebido, devendo providenciar toda a manutenção preventiva e corretiva, as suas expensas, no período em que estiver sob sua responsabilidade. Se por ocasião da sua devolução à locadora, for verificada a necessidade de quaisquer reparos ou manutenção, a locatária se responsabilizará por todas as despesas do mesmo.<br/><br/>
        6.11.	Está entendido entre as partes que a locadora não será responsável por qualquer perda, atraso ou prejuízo de qualquer natureza, inclusive lucros cessantes, resultados de defeitos, ineficácia ou quebra acidental do bem locado, objeto desta proposta. Os riscos pessoais ou materiais da locatária ou de terceiros, decorrentes da utilização do bem locado, serão de exclusiva e integral responsabilidade da locatária.<br/><br/>
        6.12.	Manter o equipamento no local exato da instalação. Qualquer mudança só será permitida mediante o prévio consentimento por escrito da locadora. Ficando a critério exclusivo desta a mudança de uma cidade para outra. Quaisquer despesas decorrentes dessas mudanças de local, inclusive, mas não exclusivamente, transporte, montagem, colocação do equipamento no novo local indicado e novas instalações elétricas, correm por conta exclusiva da locatária.<br/><br/>

            '''
        )

        p.wrapOn(cnv,500,25)
        p.drawOn(cnv,35,120)

        cnv.drawImage(R"C:/ekoos_contratos_api/functions/footer.jpeg",10,0)

        cnv.showPage()

    
        cnv.drawImage("C:/ekoos_contratos_api/functions/cabeçalho.jpeg",30,710,width=550)

        p = Paragraph(
            '''
            6.13.	Defender e fazer valer todos os direitos de propriedade e de posse da locadora sobre o equipamento, inclusive impedindo sua penhora, sequestro, arresto, arrecadação, etc., por terceiros, notificando-os sobre os direitos de propriedade e de posse da locadora sobre o equipamento, e não permitir que terceiros não autorizados ou não credenciados pela locadora intervenham nas partes e nos componentes internos do equipamento.<br/><br/>
        6.14.	Comunicar imediatamente a locadora qualquer intervenção ou violação por terceiros de qualquer dos seus direitos em relação ao equipamento.<br/><br/>
        6.15.	Por ocasião da devolução do bem locado, a locatária deverá ter necessariamente a nota fiscal de retorno e está presente um preposto da locatária com poderes bastante, para assistir à verificação e tomar ciência de eventuais danos constatados, ou falta de componentes, bem como assinar o termo de devolução do bem locado. A ausência de qualquer preposto da locatária valera como concordância do termo de devolução do bem locado necessitando de reparos ou manutenções, correrá por conta da locataria<br/><br/>
        6.16.	Responsabiliza-se por qualquer dano, prejuízo ou inutilização do equipamento, ressalvadas as hipóteses de casos fortuitos ou de força maior, bem como pelo descumprimento de qualquer de suas obrigações previstas neste contrato ou em lei.<br/><br/>


        <b>7.	Disposições Gerais</b><br/><br/>

        7.1.	Não estabelece entre as partes o presente contrato qualquer forma de sociedade, associação, vínculo empregatício da Locatária com relação aos empregados da Locadora ou responsabilidade conjunta ou solidaria de qualquer tipo.<br/><br/>
        7.2.	Na possibilidade deste contrato de ser estendido por prazo superior a 12 (doze) meses, o valor da locação será automaticamente reajustado pelo índice do IGP-M (Índice Geral de Preços de Mercado), ou outro que vier a substitui-lo e que reflita a correspondente atualização. Caso Locatária deseje encerrar antecipadamente a locação, no período anterior a eventual prorrogação automática do contrato, a Locadora fará jus à remuneração de 50% (cinquenta por cento) do valor que seria devido até o termino da locação.<br/><br/>
        7.3.	Na Ocorrência de qualquer hipótese descrita no item 4.6, a Locatária pagará à Locadora o valor fixado na Nota Fiscal de Remessa dos Equipamentos, ou pagará o valor correspondente aos reparos, caso o(s) equipamento(s), venham a comportar tais reparos.Na seguinte situação que a Locatária não efetuar pagamento indenizatório ou reparatório que refere-se ao(s) equipamento(s) o Locador irá permanecer cobrando da Locatária o valor da locação referente ao período contratado, onde este valor será utilizado para as despesas do(s) reparo(s) do(s) equipamento(s) que foi(ram) locado(s) e retornou(aram) danificado(s) ou foi(ram) furtado(s).<br/><br/>
        7.4.	Em qualquer hipótese de extinção do contrato, ocorrendo recusa pela Locatária em devolver o(s) bem(ns) à Locadora, esta poderá valer-se do disposto no artigo 1.210, parágrafo 1º, do Código civil, e retirar por seus próprios meios e condições o(s) equipamento(s), onde quer que sejam, independentemente de qualquer formalidade, aviso, notificação ou interpelação. Neste caso, toda despesa incorrida pela Locadora para desmontagem, carregamento, transporte e descarregamento dos equipamentos, mas não se limitando a estas, será de responsabilidade da Locatária, inclusive diárias do equipamento.<br/><br/>

            '''
        )

        p.wrapOn(cnv,500,25)
        p.drawOn(cnv,35,120)

        cnv.drawImage(R"C:/ekoos_contratos_api/functions/footer.jpeg",10,0)

        cnv.showPage()


    
        cnv.drawImage("C:/ekoos_contratos_api/functions/cabeçalho.jpeg",30,710,width=550)

        p = Paragraph(
            '''
            7.5.	As partes ajustam que, na infração de qualquer das cláusulas contratuais por parte da Locatária, a Locadora poderá, além de rescindir este contrato, como previsto acima, exigir e obter imediata devolução do equipamento, cabendo-lhe inclusive, na via judicial, a reintegração “initio litis”, valido para os fins do inciso II e III do artigo 927 do código de Processo Civil, o documento enviado pela Locadora solicitando a devolução do equipamento.<br/><br/>
            7.6.	Qualquer uma das partes (Locadora ou Locatária) presentes neste contrato, poderá renuciar o mesmo a qualquer momento desde que ambos estejam em dias, Locatária as devidas cobranças de periodo(s) anterior(es) esteja(m) em dias com Locadora. Locadora cumprir até período pré estabelecido com o cliente o serviço contratado, sem ônus para Locatária e Locadora.<br/><br/>
            
            <b>8.	Foro:</b><br/><br/>
            Esta proposta após aceita passa a ser um contrato e fica eleito o foro da cidade de Luis Eduardo Magalhães - BA que será competente para dirimir as questões decorrentes do presente contrato, ou sua execução. Em caso de descumprimento de qualquer das cláusulas descritas no presente contrato, o equipamento locado poderá ser retirado por seu legítimo proprietário do local onde se encontra. Estamos à disposição para quaisquer esclarecimentos adicionais<br/><br/>
            '''
        )

        p.wrapOn(cnv,500,25)
        p.drawOn(cnv,35,465)


        data_hoje = str(datetime.now())
        
        
        cnv.drawCentredString(290,430,f"Luis Eduardo Magalhães – BA, {data_hoje[8:11]} de {data(data_hoje[5:7])} de {data_hoje[:4]}")
        cnv.drawImage(R"C:/ekoos_contratos_api/functions/footer.jpeg",10,0)

        cnv.line(50,365,220,365)

        cnv.line(380,365,550,365)

        cnv.drawString(100,350,"LOCATÁRIA")
        cnv.drawString(430,350,"LOCADORA")

        #cnv.drawImage(r"C:/ekoos_contratos_api/functions/footer.jpeg",10,0)
        cnv.save()

    gera_contrato_sub(seq_contrato=seq_contrato)


        
    