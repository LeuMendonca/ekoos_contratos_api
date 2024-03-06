from ninja import Router
from django.db import connection
from datetime import datetime , timezone

router = Router()

@router.get('clientes')
def getClientes(request):
    cursor = connection.cursor()

    cursor.execute('select cod_pessoa , nome from ek_pessoa order by cod_pessoa')

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

    cursor.execute('select cod_produto , desc_produto from ek_produto order by cod_produto limit 50')

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

@router.post('new-contract')
def newContract( request, data , listItems ):
    cursor = connection.cursor()

    cursor.execute(f'''
                        insert into public.ek_contrato(
                            num_empresa, cod_pessoa, numero_contrato, vl_contrato, dt_inicio_contrato, dt_fim_contrato, dt_cadastro, status, combustivel, qtd_combustivel, cabos, chave_transf_manual, chave_transf_auto, transporte, instalacao, manutencao, distancia_transporte, franquia, carga_horaria
                        ) values (
                            {data.num_empresa},{data.cod_pessoa},{data.num_contrato},{data.vl_contrato},{data.dt_inicio_contrato},{data.dt_fim_contrato},now(), 'A' , {data.combustivel},{data.qtd_combustivel},{data.cabos},{data.chv_trans_manual},{data.chv_trans_auto},{data.transporte},{data.instalacao},{data.manutencao},{data.distancia_transporte},{data.franquia},{data.carga_horaria}
                        ) returning seq_contrato
                   ''')
    seq_contrato = cursor.fetchall()[0]
    
    for item in listItems:

        cursor.execute(f"select desc_produto from ek_produto where cod_produto = {item.cod_produto}")
        desc_produto = cursor.fetchall()[0][0]

        cursor.execute(f'''
                       INSERT INTO public.ek_contrato_detalhe(
                             seq_contrato, cod_produto, desc_item_contrato, vl_item_contrato, quantidade, unid_medida)
                            VALUES ({seq_contrato}, {item.cod_produto}, {desc_produto}, {item.vl_item_contrato}, {item.quantidade}, {item.unid_medida});
                       
                       ''')