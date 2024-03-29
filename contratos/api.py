from ninja import Router , Schema
from django.db import connection
from datetime import datetime
from typing import List
import json

import os
from django.conf import settings
from django.http import HttpResponse
from funcoes.gera_contrato import *

router = Router()

# Schema para mensagem de erro do response.
class Message(Schema):
    message: str

def formatCapitalize(fullName):
    return ' '.join(list(map(lambda x: x.capitalize() , fullName.split())))

@router.get('auth')
def Authentication(request , user , password , company):
    cursor = connection.cursor()

    cursor.execute(f"""select nome_usuario, cod_usuario , (select nome_empresa from ek_empresa where num_empresa = {company}) from ek_usuario
                   where nome_usuario = '{user}' and senha = '{password}'""")
    userLogin = cursor.fetchall()

    if userLogin:
        dataUserLogin = {
            "name": formatCapitalize(str(userLogin[0][0])),
            "codUser": userLogin[0][1],
            "company": company,
            "nameCompany": userLogin[0][2]
        }

        return {'status': 200 , 'message' : 'Login efetuado com sucesso.' , 'data': dataUserLogin}
    return { 'status' : 404 , 'message' : 'Usuário inexistente'}
        
        
@router.get('empresas')
def getEmpresas(request):
    cursor = connection.cursor()

    cursor.execute('select num_empresa::varchar , nome_empresa from ek_empresa order by num_empresa')
    resEmpresa = cursor.fetchall()

    listEmpresa = []

    for empresa in resEmpresa:
        listEmpresa.append({
            'value' : empresa[0],
            'label' : empresa[1] 
        })
    return listEmpresa

@router.get('nome-empresa/{num_empresa}')
def getNomeEmpresa(request, num_empresa: str):
    cursor = connection.cursor()

    cursor.execute(f'select nome_empresa from ek_empresa where num_empresa = {num_empresa}')
    nameEmpresa = cursor.fetchall()[0][0]
    print(nameEmpresa)

    return { "nome_empresa" : nameEmpresa }

@router.get('clientes')
def getClientes(request):
    cursor = connection.cursor()

    cursor.execute('''
                        (select 0 as cod_pessoa, 'Selecione o cliente' as nome)

                                            UNION ALL

                        (select cod_pessoa, nome from ek_pessoa order by cod_pessoa)
                ''')

    resPessoa = cursor.fetchall()

    listPessoa = []

    for pessoa in resPessoa:
        listPessoa.append({
            'value' : pessoa[0],
            'label' : pessoa[1] 
        })
    
    return listPessoa

@router.get('produtos')
def getProdutos(request):
    cursor = connection.cursor()

    cursor.execute('''
                        (
                            select '0' as cod_produto, 'Selecione um produto' as desc_produto
                        )

                                                 UNION ALL

                        ( 
                            select cod_produto::varchar , desc_produto 
                                from ek_produto 
                            where cod_produto <> 321 and tipo_item = 9 order by cod_produto::integer )
                    ''')

    resProduto = cursor.fetchall()

    listProduto = []

    for produto in resProduto:
        listProduto.append({
            'value' : produto[0],
            'label' : produto[1] 
        })
    
    return listProduto

@router.get('/produtos-descricao/{cod_produto}')
def getDescProduto(request, cod_produto:int):
    cursor = connection.cursor()

    cursor.execute(f"select desc_produto from ek_produto where cod_produto = {cod_produto}")
    desc_produto = cursor.fetchall()[0][0]

    return {"desc_produto" : desc_produto}

@router.get('contratos')
def getContratos(request , query = '' , offset = 0 , num_empresa = 1):
    cursor = connection.cursor()
    
    resContratos = None
    paginacaoContratos = None

    print(num_empresa)

    if not query:
        cursor.execute(f'''
                            select 
                            ek_contrato.seq_contrato,
                            ek_contrato.cod_pessoa,
                            ek_pessoa.nome,
                            ek_contrato.vl_contrato,
                            substring(replace(ek_contrato.dt_inicio_contrato::text,'-','/') from 0 for 11)::date,
                            substring(replace(ek_contrato.dt_fim_contrato::text,'-','/') from 0 for 11)::date,
                            ek_contrato.dt_fim_contrato < now() as "vencido"
                            from ek_pessoa inner join ek_contrato on ek_pessoa.cod_pessoa = ek_contrato.cod_pessoa
                            where ek_contrato.status = 'A'
                            and num_empresa = {num_empresa}
                            order by seq_contrato desc
                            limit 10
                            offset {offset}
                    ''')
        resContratos = cursor.fetchall()
        
        cursor.execute(f'''
                        select 
                        count(*) as "Total Contratos",
                        ceiling(count(*)::double precision/10) as "Quantia de paginas"
                        from ek_pessoa inner join ek_contrato on ek_pessoa.cod_pessoa = ek_contrato.cod_pessoa
                        where ek_contrato.status = 'A'
                        and num_empresa = {num_empresa}
                       ''')
        paginacaoContratos = cursor.fetchall()
    else:
        cursor.execute(f'''
                            select 
                                ek_contrato.seq_contrato,
                                ek_contrato.cod_pessoa,
                                ek_pessoa.nome,
                                ek_contrato.vl_contrato,
                                substring(replace(ek_contrato.dt_inicio_contrato::text,'-','/') from 0 for 11)::date,
                                substring(replace(ek_contrato.dt_fim_contrato::text,'-','/') from 0 for 11)::date,
                                ek_contrato.dt_fim_contrato < now() as "vencido"
                            from ek_pessoa inner join ek_contrato on ek_pessoa.cod_pessoa = ek_contrato.cod_pessoa
                            where 
                                ek_pessoa.nome like '%{query.upper()}%' 
                                and ek_contrato.status = 'A'
                                and ek_contrato.num_empresa = {num_empresa}
                            order by seq_contrato desc
                            limit 10
                            offset {offset}
                    ''')
        resContratos = cursor.fetchall()
        
        cursor.execute(f"""
                    select 
                    count(*) as "Total Contratos",
                    ceiling(count(*)::double precision/10) as "Quantia de paginas"
                    from ek_pessoa inner join ek_contrato on ek_pessoa.cod_pessoa = ek_contrato.cod_pessoa
                    where ek_pessoa.nome like '%{query.upper()}%' 
                    and ek_contrato.status = 'A'
                    and ek_contrato.num_empresa = {num_empresa}
                   """)
        paginacaoContratos = cursor.fetchall()
        
    listContratos = []

    for contrato in resContratos:
        listContratos.append({
            'seq_contrato' : contrato[0],
            'cod_pessoa' : contrato[1],
            'name' : contrato[2],
            'currencyContract' : contrato[3],
            'dateStart' : datetime.strftime(contrato[4] , "%d/%m/%Y"),
            'dateEnd' : datetime.strftime(contrato[5] , "%d/%m/%Y"),
            'vencido' : contrato[6]
        })

    jsonContratos = {
        'listContratos': listContratos,
        'paginationContracts': {
            'totalContracts' : paginacaoContratos[0][0],
            'totalPages' : paginacaoContratos[0][1]
        }
    }
    
    jsonContratos = json.dumps(jsonContratos)
    
    return  jsonContratos

@router.get('get-contract-id/{seq_contrato}')
def getContrctID(request,seq_contrato:int):
    def separaContract(lista):
        return {
            'seq_contrato': lista[0], 
            'client': lista[1], 
            'totalPriceContract': lista[2], 
            'initialDate': lista[3], 
            'finalDate': lista[4], 
            'franchise': str(lista[5]), 
            'hours': str(lista[6]), 
            'transporte': lista[7], 
            'combustivel': lista[8], 
            'chvTransManual': lista[9], 
            'chvTransAuto': lista[10], 
            'instalacao': lista[11], 
            'manutencaoPeriodica': lista[12], 
            'cabos': lista[13],
            'distanciaTransporte': lista[14],
            'quantidadeCombustivel': lista[15]
        }

    def separaDetalhes(lista):
        return {
            'id' : lista[0],
            'seq_contrato_detalhe' : lista[1],
            'product' : lista[3],
            'descProduct' : lista[4],
            'unitPrice' : lista[5],
            'amount' : lista[6],
            'unit' : lista[7],
        }

    cursor = connection.cursor()

    cursor.execute(f'''
                    select 
                        seq_contrato, 
                        cod_pessoa,
                        vl_contrato, 
                        dt_inicio_contrato::date, 
                        dt_fim_contrato::date, 
                        franquia, 
                        carga_horaria, 
                        transporte, 
                        combustivel, 
                        chave_transf_manual, 
                        chave_transf_auto, 
                        instalacao, 
                        manutencao, 
                        cabos,
                        distancia_transporte,
                        qtd_combustivel
                    from ek_contrato
                    where seq_contrato = {seq_contrato}
                ''')
    contractID = cursor.fetchall()
    contractID = list(map(separaContract , contractID))

    cursor.execute(f'''
                    select 
                        ROW_NUMBER() OVER () AS id,
                        seq_contrato_detalhe, 
                        seq_contrato, 
                        cod_produto, 
                        desc_item_contrato, 
                        vl_item_contrato, 
                        quantidade, 
                        unid_medida
                    from ek_contrato_detalhe
                    where seq_contrato = {seq_contrato}
                   ''')
    contractIDDetalhes = cursor.fetchall()
    contractIDDetalhes = list(map(separaDetalhes , contractIDDetalhes))
    

    
    return {
        'contract': contractID[0],
        'contractDetails': contractIDDetalhes
    }

# ----------------------------------------------------------------------------------------------------------------
class Itens(Schema):
    id: int = 0
    seq_contrato: int = 0
    seq_contrato_detalhe: int = 0
    product: int
    descProduct: str 
    unitPrice: float
    amount: int
    unit: str

class Contrato(Schema):
    num_contrato: int = 0
    totalPriceContract: int = 0
    client: int 
    company: int = 1
    franchise: str 
    hours: str 
    initialDate: str 
    finalDate: str 
    cabos: bool = False
    chvTransAuto: bool = False
    chvTransManual: bool = False
    combustivel: bool = False
    quantidadeCombustivel: float = 0
    instalacao: bool = False
    manutencaoPeriodica: bool = False
    transporte: bool = False
    distanciaTransporte: float = 0
    # listItems: List[Itens]


@router.post('new-contract',response={200:Message , 404:Message})
def newContract( request ,data: Contrato , listItems: List[Itens] ):
    cursor = connection.cursor()

    if datetime.fromisoformat(data.initialDate) > datetime.fromisoformat(data.finalDate):
        return 404 , {"message" : "Data inicial é maior que a data final"}

    try:
        cursor.execute(f'''
                            insert into ek_contrato(
                                num_empresa, cod_pessoa, vl_contrato, dt_inicio_contrato, dt_fim_contrato, dt_cadastro, status, combustivel, qtd_combustivel, cabos,chave_transf_manual, chave_transf_auto, transporte, instalacao, manutencao, distancia_transporte, franquia, carga_horaria
                            ) values (
                                {data.company},{data.client},{data.totalPriceContract},'{data.initialDate + ' 12:00'}','{data.finalDate + ' 12:00'}', now() ,'A' , {data.combustivel},{data.quantidadeCombustivel},{data.cabos},{data.chvTransManual},{data.chvTransAuto},{data.transporte},{data.instalacao},{data.manutencaoPeriodica},{data.distanciaTransporte},{data.franchise},{data.hours}
                            ) returning seq_contrato
                    ''')
        seq_contrato = cursor.fetchall()[0][0]

        for item in listItems:

            cursor.execute(f'''
                        INSERT INTO public.ek_contrato_detalhe(
                                seq_contrato, cod_produto, desc_item_contrato, vl_item_contrato, quantidade, unid_medida)
                                VALUES ({seq_contrato}, {item.product}, '{item.descProduct}', {item.unitPrice}, {item.amount}, '{item.unit}');
                        ''')
            

        cursor.execute(
                    f'''
                        insert into ek_pedido_Cli(
                            dt_pedido,
                            flag_status,
                            vl_total_pedido,
                            cod_pessoa,
                            tipo_pedido,
                            dt_cadastro,
                            num_empresa,
                            obs_pedido,
                            numero_contrato
                        )values(
                            '{datetime.now()}',
                            'F',
                            {data.totalPriceContract},
                            {data.client},
                            'P',
                            '{datetime.now()}',
                            { data.company },
                            'Pedido gerado através do contrato',
                            {seq_contrato}
                        )
                    '''
                )

        cursor.execute(f'''
                            select dt_inicio_contrato , dt_fim_contrato 
                            from ek_contrato 
                            where seq_contrato = {seq_contrato}
                        ''')
        data = cursor.fetchall()[0]
        dias_contrato = abs((data[1] - data[0]).days)
        
        
        cursor.execute(f'select max(seq_item_pedido) from ek_item_pedido_cli')
        max_seq_item_pedido = cursor.fetchall()[0][0]
        
        cursor.execute(f'''select seq_pedido_cli 
                        from ek_pedido_cli 
                        where numero_contrato = {seq_contrato}''')
        seq_pedido_cli = cursor.fetchall()[0][0]

    except:
        return 404,{"message" : "Houve um problema ao gravar a capa do contrato."}

    try:
        cursor.execute(f'''select * from 
                        ek_contrato_detalhe 
                        where seq_contrato = {seq_contrato}
                    ''')
        resDetalheContrato = cursor.fetchall()

        start = 1

        for res in resDetalheContrato:
            max_seq_item_pedido += 1
            cursor.execute(f'''select desc_produto 
                                from ek_produto 
                                where cod_produto = {res[2]}''')
            desc = cursor.fetchall()[0]
            
            cursor.execute(f'''insert into ek_item_pedido_cli(
                            seq_pedido_cli,
                            cod_item,
                            qtd_pedido,
                            qtd_atendido,
                            vl_unitario,
                            vl_total_item,
                            dt_cadastro,
                            seq_item_pedido,
                            status_item,
                            sequencia_item,
                            desc_item
                        )values(
                            {seq_pedido_cli},
                            {res[2]},
                            1,
                            1,
                            {res[4] * res[5]},
                            {res[4] * res[5]},
                            '{datetime.now()}',
                            {max_seq_item_pedido},
                            'F',
                            {start},
                            'Locacao produto {res[2]} - {desc[0]} - {dias_contrato} dias - Valor Total: {dias_contrato * res[4]}'
                        )
                        ''')
            start += 1    

            return 200 , {"message" : f"Contrato {seq_contrato} cadastrado com sucesso!"}     
    except:
        return 404,{"message" : "Houve um problema ao gravar os itens dos contrato."}

@router.put('update-contract/{seq_contrato}' , response={200: Message , 404: Message })
def updateContract( request , seq_contrato:int ,data: Contrato , itens: List[Itens]):

    print( data )
    
    cursor = connection.cursor()

    if datetime.fromisoformat(data.initialDate) > datetime.fromisoformat(data.finalDate):
        return 404 , {"message" : "Data inicial é maior que a data final"}

    try:
        cursor.execute(f'''
                    UPDATE ek_contrato
                        SET cod_pessoa = { data.client },  
                            vl_contrato = { data.totalPriceContract},
                            dt_inicio_contrato = '{ data.initialDate }' , 
                            dt_fim_contrato = '{ data.finalDate }', 
                            franquia = { data.franchise } , 
                            carga_horaria = { data.hours },                        
                            transporte = { data.transporte }, 
                            combustivel = { data.combustivel }, 
                            chave_transf_manual = { data.chvTransManual }, 
                            chave_transf_auto = { data.chvTransAuto }, 
                            instalacao = { data.instalacao }, 
                            manutencao = { data.manutencaoPeriodica }, 
                            cabos = { data.cabos },
                            distancia_transporte = { data.distanciaTransporte },
			                qtd_combustivel = { data.quantidadeCombustivel }
                        WHERE seq_contrato = { seq_contrato };
                    ''')

        cursor.execute(f'''
                        select seq_contrato_detalhe from ek_contrato_detalhe where seq_contrato = {seq_contrato}
                    ''')
        resContratoDetalhe = cursor.fetchall()
        resContratoDetalhe = list(map(lambda x: x[0] , resContratoDetalhe))

        for item in itens:
                if item.seq_contrato_detalhe in resContratoDetalhe:
                    cursor.execute(f'''
                                    UPDATE ek_contrato_detalhe
                                    SET
                                        cod_produto = {item.product}, 
                                        desc_item_contrato = '{item.descProduct}', 
                                        vl_item_contrato = {item.unitPrice}, 
                                        quantidade = {item.amount} , 
                                        unid_medida =  '{item.unit}'
                                    WHERE seq_contrato = {seq_contrato} and seq_contrato_detalhe = {item.seq_contrato_detalhe};
                                    ''')
                    resContratoDetalhe.remove(item.seq_contrato_detalhe)
                else:
                    cursor.execute(f'''
                            INSERT INTO public.ek_contrato_detalhe(
                                    seq_contrato, cod_produto, desc_item_contrato, vl_item_contrato, quantidade, unid_medida)
                                    VALUES ({seq_contrato}, {item.product}, '{item.descProduct}', {item.unitPrice}, {item.amount}, '{item.unit}');
                            ''')
        if resContratoDetalhe:
            cursor.execute(f"delete from ek_contrato_detalhe where seq_contrato_detalhe in ( {','.join(map(str , resContratoDetalhe))} )")
        return 200 , { 'message' : f'Contrato {seq_contrato} atualizado!'}
    except:
        return 404, { 'message' : 'Não foi possivel atualizar o contrato'}
        



@router.delete("delete-contract/{seq_contrato}",response={200: Message , 404: Message})
def delete(request, seq_contrato: int):
    cursor = connection.cursor()

    cursor.execute(
        f'''
            select
            coalesce(seq_nota,0) as "seq_nota",
            coalesce(seq_nota_servico,0) as "seq_nota_servico" 
            from ek_contrato  
            where seq_contrato = {seq_contrato}
        '''
    )
    atributos = cursor.fetchall()[0]

    if atributos[0] == 0 and atributos[1] == 0:
        cursor.execute(
            f'''
                update ek_contrato 
                set status = 'E' 
                where seq_contrato = {seq_contrato}
            '''
        )
        
        cursor.execute(
            f"""
                update ek_pedido_cli 
                set flag_status = 'C' , 
                obs_pedido = 'Pedido cancelado através do EkoOS Contrato {seq_contrato}' 
                where numero_contrato = {seq_contrato}
            """
        )
        
        cursor.execute(
            f"""
                update ek_item_pedido_cli set 
                status_item = 'C' 
                where seq_pedido_cli in 
                (select seq_pedido_cli from ek_pedido_cli where numero_contrato = {seq_contrato})
            """
        )

        return 200, { "message" : f'Contrato {seq_contrato} excluido!' }
    else:
        return 404, { "message" : f'Já existem notas para esse contrato!' }
    
@router.put('close-contract/{seq_contrato}',response={200: Message , 404: Message})
def fechar(request,seq_contrato):
    cursor = connection.cursor()

    cursor.execute(
        f'''
            select
            coalesce(seq_nota,0) as "seq_nota",
            coalesce(seq_nota_servico,0) as "seq_nota_servico" 
            from ek_contrato  
            where seq_contrato = {seq_contrato}
        '''
    )
    atributos = cursor.fetchall()[0]

    if atributos[0] == 0 and atributos[1] == 0:
        cursor.execute(
            f'''
                update ek_contrato 
                set status = 'F' 
                where seq_contrato = {seq_contrato}
            '''
        )
        
        cursor.execute(
            f"""
                update ek_pedido_cli 
                set flag_status = 'F' , 
                obs_pedido = 'Pedido cancelado através do EkoOS Contrato {seq_contrato}' 
                where numero_contrato = {seq_contrato}
            """
        )
        
        cursor.execute(
            f"""
                update ek_item_pedido_cli set 
                status_item = 'F',qtd_atendido = qtd_pedido
                where seq_pedido_cli in 
                (select seq_pedido_cli from ek_pedido_cli where numero_contrato = {seq_contrato})
            """
        )
        return 200, { "message" : f'Contrato {seq_contrato} fechado!' }
    else:
        return 404, { "message" : f'Já existem notas para esse contrato!' }
            
@router.post('generate-invoice/{seq_contrato}', response={200: Message,404:Message})
def gera_nota_remessa(request, seq_contrato:int):
    
    cursor = connection.cursor()

    cursor.execute(
        f'''
            select
                coalesce(seq_nota,0) as "seq_nota"
            from ek_contrato 
            where seq_contrato = {seq_contrato}
        '''
    )
    seq_nota_remessa = cursor.fetchall()[0][0]

    if seq_nota_remessa == 0:

        cursor.execute(
                f'''
                select cod_pessoa,vl_total_pedido 
                from ek_pedido_cli 
                where numero_contrato = {seq_contrato}
                '''
                )
        try:
            pedido = cursor.fetchall()[0]
        except:
            return 404,{ 'message' : f'Não existe pedidos para o contrato {seq_contrato}'}

        if pedido:
        
            cursor.execute(
                    f'''update ek_configuracao 
                    set num_doc_controle = num_doc_controle + 1  
                    where num_empresa = 1 
                    returning num_doc_controle'''
                    )
            num_doc_controle = cursor.fetchall()[0][0]
                
            cursor.execute(
            f'''
            select seq_pessoa_inscricao_estadual 
            from ek_pessoa_incricao_estadual 
            where cod_pessoa = {pedido[0]} 
            and insc_fiscal = 'S' 
            limit 1
            '''
            )
            seq_pessoa_inscricao_estadual = cursor.fetchall()[0][0]

            cursor.execute('''
                           select
                                (case 
                                    when 
                                        (select estado from ek_empresa where num_empresa = 1) = (select estado from ek_pessoa where cod_pessoa = 2483)
                                        then 5949
                                else 6949 
                           end)
                           ''')
            cfop = cursor.fetchall()[0][0]

            
            cursor.execute(f'''select serie_nfe 
                            from ek_configuracao 
                            where num_empresa = 1''')
            serie = cursor.fetchall()[0][0]
            
            cursor.execute(
                f'''
                insert into ek_nota(
                    num_empresa,
                    ind_oper,   
                    ind_emit,
                    cod_part,
                    cod_mod,
                    ser,
                    num_doc,
                    dt_doc,
                    dt_e_s,
                    vl_doc,
                    vl_merc,
                    cod_mov,
                    dt_cadastro,
                    cfop,
                    cod_sit,
                    desc_complementar,
                    seq_pessoa_inscricao_estadual
                )values(
                    1,
                    '1',
                    '0',
                    {pedido[0]},
                    '55',
                    '{serie}',
                    {num_doc_controle},
                    '{datetime.now()}',
                    '{datetime.now()}',
                    {pedido[1]},
                    {pedido[1]},
                    '2',
                    '{datetime.now()}',
                    '{cfop}',
                    '00',
                    'Nota fiscal de remessa locacao referente ao contrato {seq_contrato}.',
                    {seq_pessoa_inscricao_estadual}
                    ) returning seq_nota
                    '''
            )

            seq_nota = cursor.fetchall()[0][0]

            cursor.execute(
                f'''
                    select * 
                    from ek_item_pedido_cli 
                    where seq_pedido_cli in 
                    (select seq_pedido_cli from ek_pedido_cli where numero_contrato = {seq_contrato})
                '''
            )

            ek_item_pedido_cli = cursor.fetchall()
            
            
            seq_item = 0
            for x in ek_item_pedido_cli:
                cursor.execute(
                f'''
                select unid_venda , desc_produto 
                from ek_produto 
                where cod_produto = {x[1]}
                '''
                )
                produto = cursor.fetchall()[0]
            
                
                seq_item = seq_item + 1
                cursor.execute(f'''
                    insert into ek_item_nota (
                    seq_nota,
                    seq_item, 
                    cod_item,
                    quantidade,
                    unidade,
                    vl_item,
                    cst_icms,
                    cfop,
                    dt_cadastro,
                    vl_total_item,
                    desc_item_nota
                    )values(
                        {seq_nota},
                        {seq_item},
                        127,
                        {x[2]},
                        '{produto[0]}',
                        {x[10]},
                        '090',
                        '{cfop}',
                        '{datetime.now()}',
                        {x[11]},
                        '{produto[1]}'
                    )
                ''')

                    
                
                cursor.execute(f'''
                                update ek_item_pedido_cli 
                                set seq_nota = {seq_nota} 
                                where seq_pedido_cli in 
                                (select seq_pedido_cli from ek_pedido_cli where numero_contrato = {seq_contrato})
                            ''')
                
            
            cursor.execute(f'''update ek_contrato 
                            set seq_nota = {seq_nota} 
                            where seq_contrato = {seq_contrato}''')
        
            return 200,{ 'message' : 'Nota fiscal gerada com sucesso!'}
        
            
    else:
        return 404 , {'message' :  f'Nota fiscal já foi gerada!!' }
    

@router.post('generated-service-invoice/{seq_contrato}',response={200: Message , 404: Message})
def gera_nota_servico(request,seq_contrato:int):
    cursor = connection.cursor()
    
    cursor.execute(f'''select count(*) 
                    from ek_pedido_cli 
                    where numero_contrato = {seq_contrato}''')
    confere_pedido = cursor.fetchall()[0][0]

    if confere_pedido == 0:
        return 404,{ 'message' : f'Não existe pedidos para o contrato {seq_contrato}'}
    else:
        cursor = connection.cursor()
        
        cursor.execute(
            f"""select 
                    coalesce(seq_nota_servico, 0) as "seq_nota_servico"
                from ek_contrato 
                where seq_contrato = {seq_contrato}"""
        )
        
        seq_nota_servico = cursor.fetchall()[0][0]

        if seq_nota_servico == 0:
            cursor.execute(f'''select seq_pedido_cli 
                            from ek_pedido_cli 
                            where numero_contrato = {seq_contrato}''')
            pedido = cursor.fetchall()[0][0]
            
            
            cursor = connection.cursor()
            cursor.execute(f'''select * from gera_nota_fiscal({pedido})''')
            seq_nota_servico = cursor.fetchall()[0][0]
            
            cursor.execute(
                f'''
                    update ek_contrato 
                    set seq_nota_servico = {seq_nota_servico} 
                    where seq_contrato = {seq_contrato}
                '''
            )
            
            cursor.execute(f'''update ek_contrato set status = 'F' where seq_contrato = {seq_contrato}''')

            return 200,{'message' , f'Nota de serviço gerada com sucesso!'}
        else:
            return 404,{'message' , f'Já existe uma nota de serviço para o contrato!'}

@router.get('print-contract/{seq_contrato}')
def gerador_contrato(request,seq_contrato):
    
    caminho ="c:/Projetos/ekoos_contratos_api/midia/Contrato-"+ str(seq_contrato) + '.pdf'
    caminho = os.path.join(settings.MEDIA_ROOT,caminho)

    gera_contrato(caminho,seq_contrato,connection)
    
    
    if os.path.exists(caminho):
        with open(caminho,'rb') as fh:
            response = HttpResponse(fh.read(),content_type="application/pdf")
            response['Content-Disposition'] = 'inline;filename=' + os.path.basename(caminho)
        os.remove(caminho)
        return response