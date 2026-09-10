"""Teste sintetico, exclusivamente --background --factory-startup. Sem socket."""
import json
import math
import os
from pathlib import Path
import sys
import unittest

import bpy
import bmesh

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(os.environ.get('PACOTE_MODELAGEM_3D') or Path(__file__).resolve().parents[1]/'produto')/'scripts'))
import edicao_guiada as G


def painel(nome):
    vertices = [(x,y,0) for x in (-3,-1,1,3) for y in (-1,1)]
    faces = []
    for i in range(3):
        a=2*i
        faces.extend([(a,a+2,a+3),(a,a+3,a+1)])
    me=bpy.data.meshes.new(nome);me.from_pydata(vertices,[],faces);me.update()
    ob=bpy.data.objects.new(nome,me);bpy.context.collection.objects.link(ob)
    return ob


class Edicao(unittest.TestCase):
    def setUp(self):
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj,do_unlink=True)
        bpy.context.scene.unit_settings.system='METRIC'
        bpy.context.scene.unit_settings.scale_length=.001
        self.obj=painel('Painel_sintetico')
        bpy.context.view_layer.objects.active=self.obj;self.obj.select_set(True)
        self.antes=G.captura(self.obj.name)
        self.plano={'assinatura_antes':self.antes['sha256'],'alvo':[6,7],
                    'transicao':[[2,1/3],[3,1/3],[4,2/3],[5,2/3]],'vetor':[0,0,1]}
        self.limites={'area_min':12.16,'area_max':12.17,'angulo_max_graus':.1,'qualidade_min':.04}

    def aplicar(self):return G.desloca_com_pesos(self.obj.name,self.plano)['depois']

    def test_plano_secoes_e_regiao_protegida(self):
        depois=self.aplicar()
        r=G.verifica_deslocamento(self.antes,depois,self.plano,1e-5,self.limites)
        self.assertEqual(r['estado'],'MEDIDAS_CONFORMES')
        self.assertLess(r['erro_max_protegido'],1e-8)
        # Oraculo independente: funcao analitica de uma superficie plana, nao pesos lidos da receita.
        for x,y,z in depois['vertices']:
            self.assertAlmostEqual(z,(x+3)/6,places=6)
        self.assertAlmostEqual(r['transicao_depois']['area_total'],2*math.sqrt(37),places=5)

    def test_alvo_certo_transicao_errada_reprova_so_dobra(self):
        self.plano['transicao']=[[2,.01],[3,.01],[4,.99],[5,.99]]
        depois=self.aplicar()
        limites=dict(self.limites,area_min=0,area_max=100,qualidade_min=0,angulo_max_graus=1)
        r=G.verifica_deslocamento(self.antes,depois,self.plano,1e-5,limites)
        self.assertEqual(r['estado'],'REPROVADA')
        self.assertEqual(r['falhas'],['DOBRA_DA_TRANSICAO_FORA'])
        self.assertLess(r['erro_max_alvo'],1e-8)

    def test_sem_criterio_nao_aprova(self):
        r=G.verifica_deslocamento(self.antes,self.aplicar(),self.plano,1e-5)
        self.assertEqual(r['estado'],'INDETERMINADA')

    def test_protegido_mudou(self):
        depois=self.aplicar();depois['vertices'][0][2]=.3
        r=G.verifica_deslocamento(self.antes,depois,self.plano,1e-5,self.limites)
        self.assertIn('REGIAO_PROTEGIDA_MUDOU',r['falhas'])

    def test_indices_nao_sobrevivem_a_retesselacao(self):
        depois=self.aplicar();depois['faces'][0]=list(reversed(depois['faces'][0]))
        r=G.verifica_deslocamento(self.antes,depois,self.plano,1e-5,self.limites)
        self.assertEqual(r['estado'],'INDETERMINADA')

    def test_hash_velho_recusa_sem_escrita(self):
        self.plano['assinatura_antes']='velho'
        with self.assertRaisesRegex(ValueError,'ESTADO_MUDOU'):self.aplicar()
        self.assertEqual(G.captura(self.obj.name)['sha256'],self.antes['sha256'])

    def test_peso_invalido_recusa_sem_escrita(self):
        self.plano['transicao'][0][1]=float('nan')
        with self.assertRaisesRegex(ValueError,'PESO_INVALIDO'):self.aplicar()
        self.assertEqual(G.captura(self.obj.name)['sha256'],self.antes['sha256'])

    def test_copia_preserva_materiais(self):
        material=bpy.data.materials.new('Material_sintetico')
        self.obj.data.materials.append(material)
        G.copia_para_previa(self.obj.name,'Previa_sintetica')
        copy=bpy.data.objects['Previa_sintetica']
        self.assertNotEqual(copy.data,self.obj.data)
        self.assertEqual(copy.data.materials[0],material)
        self.assertEqual(G.captura(copy.name)['sha256'],self.antes['sha256'])

    def test_contexto_override_e_flags_ocultas(self):
        oculto=painel('Malha_oculta')
        for f in oculto.data.polygons:f.select=True
        oculto.hide_set(True)
        with bpy.context.temp_override(object=None,active_object=None):
            G.entra_em_edicao(self.obj.name)
        bm=bmesh.from_edit_mesh(self.obj.data)
        for v in bm.verts:v.select=False
        bm.faces.ensure_lookup_table();bm.faces[0].select_set(True)
        bmesh.update_edit_mesh(self.obj.data)
        r=G.diagnostica()
        self.assertEqual(r['estado'],'INDICACAO_DISPONIVEL')
        self.assertEqual(r['em_edicao'][0]['objeto'],self.obj.name)
        self.assertEqual(r['flags_fora_de_edicao'][0]['objeto'],oculto.name)
        self.assertAlmostEqual(r['unidade']['mm_por_unidade'],1,places=6)

    def test_selecao_vazia(self):
        G.entra_em_edicao(self.obj.name)
        bm=bmesh.from_edit_mesh(self.obj.data)
        for f in bm.faces:f.select_set(False)
        for e in bm.edges:e.select_set(False)
        for v in bm.verts:v.select_set(False)
        bmesh.update_edit_mesh(self.obj.data)
        self.assertEqual(G.diagnostica()['estado'],'SELECAO_VAZIA')

    def test_malha_compartilhada_barrada(self):
        obj=bpy.data.objects.new('Ligada',self.obj.data);bpy.context.collection.objects.link(obj)
        with self.assertRaisesRegex(ValueError,'MALHA_NAO_INDEPENDENTE'):self.aplicar()

    def test_coordenada_invalida_nao_passa(self):
        depois=self.aplicar();depois['vertices'][0][0]=float('nan')
        self.assertEqual(G.verifica_deslocamento(self.antes,depois,self.plano,1e-5,self.limites)['estado'],'INDETERMINADA')

    def test_dobra_no_encontro_com_protegido(self):
        # Faixa inclinada central entre patamares horizontais. O alvo esta certo;
        # sem os vizinhos, a faixa plana sozinha teria angulo zero e passaria.
        self.plano['alvo']=[4,5,6,7];self.plano['transicao']=[]
        depois=self.aplicar()
        lim={'area_min':0,'area_max':100,'angulo_max_graus':1,'qualidade_min':0}
        r=G.verifica_deslocamento(self.antes,depois,self.plano,1e-5,lim)
        self.assertEqual(r['falhas'],['DOBRA_DA_TRANSICAO_FORA'])
        self.assertGreater(len(r['faces_da_zona_medida']),len(r['faces_de_transicao']))

    def test_superficie_curva_nao_e_aplainada(self):
        # Nova geometria: curvatura preexistente em X, mantida por deslocamento
        # analitico superposto. Nao e prova de inferencia automatica de feicao.
        for v in self.obj.data.vertices:v.co.z=.03*v.co.x**2
        self.obj.data.update();antes=G.captura(self.obj.name)
        self.plano['assinatura_antes']=antes['sha256']
        depois=self.aplicar()
        for x,y,z in depois['vertices']:
            self.assertAlmostEqual(z,.03*x*x+(x+3)/6,places=6)


if __name__=='__main__':
    if not bpy.app.background:
        raise RuntimeError('Este teste recusa a sessao grafica do usuario')
    args=sys.argv[sys.argv.index('--')+1:]
    output=Path(args[args.index('--resultado-em')+1])
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Edicao))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'veredito_global':'ATENDIDO' if result.wasSuccessful() else 'FALHOU',
        'testes':result.testsRun,'falhas':[(str(t),s) for t,s in result.failures+result.errors],
        'blender':bpy.app.version_string},indent=2),encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
