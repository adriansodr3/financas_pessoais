# Financas Pessoais - App Android

Controle financeiro familiar no celular.

---

## Como gerar o APK pelo celular (GitHub Actions)

### Passo 1 - Criar conta no GitHub (gratuito)
1. Abra o browser do celular
2. Acesse: **github.com**
3. Clique em **Sign up**
4. Crie sua conta (email + senha)

### Passo 2 - Criar repositorio
1. Apos fazer login, clique no **+** (canto superior direito)
2. Clique em **New repository**
3. Nome: `financas-mobile`
4. Marque **Public**
5. Clique em **Create repository**

### Passo 3 - Fazer upload dos arquivos
1. Dentro do repositorio, clique em **Add file**
2. Clique em **Upload files**
3. Selecione o arquivo ZIP deste projeto
4. Aguarde o upload
5. Clique em **Commit changes**

> **Importante:** Se o upload do ZIP nao funcionar, voce precisara fazer upload
> de cada pasta separadamente. Crie as pastas clicando em
> "Create new file" e digitando `database/schema.py` no nome (isso cria a pasta).

### Passo 4 - Rodar o build
1. Clique na aba **Actions** no topo do repositorio
2. Clique em **Build APK Android** (no menu esquerdo)
3. Clique no botao **Run workflow**
4. Clique em **Run workflow** (botao verde)
5. **Aguarde 20-40 minutos** ate aparecer o circulo verde

### Passo 5 - Baixar o APK
1. Clique no build que terminou (nome com check verde)
2. Role a pagina ate **Artifacts**
3. Clique em **FinancasPessoais-APK**
4. O ZIP com o APK sera baixado no celular

### Passo 6 - Instalar no celular
1. Abra o arquivo ZIP baixado
2. Extraia o arquivo `.apk`
3. Toque no arquivo APK para instalar
4. Se aparecer "fonte desconhecida":
   - Va em **Configuracoes > Seguranca**
   - Ative **Instalar apps desconhecidos** para o seu gerenciador de arquivos
5. Toque em **Instalar**

---

## Dados do app

Os dados ficam armazenados no proprio celular, dentro do app.
Sao separados do banco de dados do computador.

---

## Funcionalidades

- Login com multiplos usuarios
- Dashboard com cards de resumo (entradas, saidas, saldo, fixos, falta pagar)
- Lancamentos mensais com navegacao por mes
- Gastos e receitas fixos (automaticos todo mes)
- Parcelamentos com quitacao e desfazer
- Categorias personalizadas
- Relatorios por categoria com barras de progresso

---

## Suporte

Em caso de erro no build, o log completo fica disponivel em
**Actions > build com erro > build-log-erro**.
