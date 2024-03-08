from ninja import Router , Schema
from django.db import connection
from datetime import datetime , timezone
import json

router = Router()

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
                        (select 0 as cod_produto, 'Selecione um produto' as desc_produto)

                                                    UNION ALL

                        (select cod_produto , desc_produto from ek_produto order by cod_produto)
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
def getContratos(request):
    cursor = connection.cursor()

    cursor.execute('''
                        select 
                        ek_contrato.seq_contrato,
                        ek_contrato.cod_pessoa,
                        ek_pessoa.nome,
                        ek_contrato.vl_contrato,
                        substring(replace(ek_contrato.dt_inicio_contrato::text,'-','/') from 0 for 11)::date,
                        substring(replace(ek_contrato.dt_fim_contrato::text,'-','/') from 0 for 11)::date
                        from ek_pessoa inner join ek_contrato on ek_pessoa.cod_pessoa = ek_contrato.cod_pessoa
                        order by seq_contrato desc
                   ''')
    
    resContratos = cursor.fetchall()

    listContratos = []

    for contrato in resContratos:
        listContratos.append({
            'seq_contrato' : contrato[0],
            'cod_pessoa' : contrato[1],
            'nome' : contrato[2],
            'vl_contrato' : contrato[3],
            'dt_inicio' : datetime.strftime(contrato[4] , "%d/%m/%Y"),
            'dt_fim' : datetime.strftime(contrato[5] , "%d/%m/%Y"),
        })
    
    return listContratos

class Contrato(Schema):
    num_empresa: int = 1
    num_contrato: int = 0
    vl_contrato: int = 0


    client: int
    franchise: str
    hours: str
    initialDate: str
    finalDate: str
    cabos: bool = False
    chvTransAuto: bool = False
    chvTransManual: bool = False
    combustivel: bool = False
    qtd_combustivel: float = 0
    instalacao: bool = False
    manutencaoPeriodicaa: bool = False
    transporte: bool = False
    distancia_transporte: float = 0


@router.post('new-contract')
def newContract( request , data: Contrato ):
    cursor = connection.cursor()

    cursor.execute(f'''
                        insert into ek_contrato(
                            num_empresa, cod_pessoa, vl_contrato, dt_inicio_contrato, dt_fim_contrato, dt_cadastro, status, combustivel, qtd_combustivel, cabos, chave_transf_manual, chave_transf_auto, transporte, instalacao, manutencao, distancia_transporte, franquia, carga_horaria
                        ) values (
                            1,{data.client},{data.vl_contrato},'{data.initialDate + ' 12:00'}','{data.finalDate + ' 12:00'}', now() ,'A' , {data.combustivel},{data.qtd_combustivel},{data.cabos},{data.chvTransManual},{data.chvTransAuto},{data.transporte},{data.instalacao},{data.manutencaoPeriodicaa},{data.distancia_transporte},{data.franchise},{data.hours}
                        ) 
                   ''')
    # seq_contrato = cursor.fetchall()[0]

    # for item in listItems:

    #     cursor.execute(f"select desc_produto from ek_produto where cod_produto = {item.cod_produto}")
    #     desc_produto = cursor.fetchall()[0][0]

    #     cursor.execute(f'''
    #                    INSERT INTO public.ek_contrato_detalhe(
    #                          seq_contrato, cod_produto, desc_item_contrato, vl_item_contrato, quantidade, unid_medida)
    #                         VALUES ({seq_contrato}, {item.cod_produto}, {desc_produto}, {item.vl_item_contrato}, {item.quantidade}, {item.unid_medida});
                       
                    #    ''')