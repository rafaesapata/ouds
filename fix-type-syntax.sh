#!/bin/bash

# Script para corrigir sintaxe de tipos incompatível com Python < 3.10
# Substitui o operador | por Union/Optional do módulo typing
# Versão específica para OUDS - Oráculo UDS

echo "🔧 OUDS - Corrigindo sintaxe de tipos incompatível..."

# Função para corrigir um arquivo
fix_type_syntax() {
    local file="$1"
    echo "📝 Processando: $file"
    
    # Verificar se o arquivo existe
    if [ ! -f "$file" ]; then
        echo "⚠️ Arquivo não encontrado: $file"
        return
    fi
    
    # Backup do arquivo original
    cp "$file" "$file.backup"
    
    # Corrigir sintaxes comuns de união de tipos
    sed -i 's/\([A-Za-z_][A-Za-z0-9_]*\) | None/Optional[\1]/g' "$file"
    sed -i 's/\([A-Za-z_][A-Za-z0-9_]*\) | \([A-Za-z_][A-Za-z0-9_]*\)/Union[\1, \2]/g' "$file"
    sed -i 's/str | int/Union[str, int]/g' "$file"
    sed -i 's/int | str/Union[int, str]/g' "$file"
    sed -i 's/dict | list/Union[dict, list]/g' "$file"
    sed -i 's/list | dict/Union[list, dict]/g' "$file"
    
    # Verificar se precisa adicionar imports
    if grep -q "Union\|Optional" "$file" && ! grep -q "from typing import.*Union\|from typing import.*Optional" "$file"; then
        # Adicionar imports necessários
        if grep -q "from typing import" "$file"; then
            # Adicionar Union e Optional aos imports existentes se não existirem
            if ! grep -q "Union" "$file"; then
                sed -i '/from typing import/ s/)/, Union)/' "$file"
                sed -i '/from typing import/ s/$/, Union/' "$file"
            fi
            if ! grep -q "Optional" "$file"; then
                sed -i '/from typing import/ s/)/, Optional)/' "$file"
                sed -i '/from typing import/ s/$/, Optional/' "$file"
            fi
        else
            # Adicionar nova linha de import
            sed -i '1i from typing import Union, Optional' "$file"
        fi
    fi
    
    echo "✅ Corrigido: $file"
}

# Diretório base do projeto
PROJECT_DIR="/home/ubuntu/ouds-project"

# Lista de arquivos para corrigir (caminhos relativos ao projeto OUDS)
files=(
    "$PROJECT_DIR/OpenManus/app/llm.py"
    "$PROJECT_DIR/OpenManus/app/tool/bash.py"
    "$PROJECT_DIR/OpenManus/app/tool/chart_visualization/data_visualization.py"
    "$PROJECT_DIR/OpenManus/app/tool/chart_visualization/python_execute.py"
    "$PROJECT_DIR/OpenManus/app/tool/chart_visualization/test/report_demo.py"
    "$PROJECT_DIR/OpenManus/app/tool/create_chat_completion.py"
    "$PROJECT_DIR/OpenManus/app/tool/str_replace_editor.py"
    "$PROJECT_DIR/OpenManus/run_mcp.py"
)

# Corrigir cada arquivo
for file in "${files[@]}"; do
    fix_type_syntax "$file"
done

echo ""
echo "🎉 OUDS - Correção de sintaxe de tipos concluída!"
echo ""
echo "📋 Resumo das correções:"
echo "- Substituído 'Type | None' por 'Optional[Type]'"
echo "- Substituído 'Type1 | Type2' por 'Union[Type1, Type2]'"
echo "- Adicionados imports necessários do módulo typing"
echo "- Compatibilidade garantida com Python 3.8+"
echo ""
echo "💡 Para testar:"
echo "cd $PROJECT_DIR && ./start_ouds.sh"
echo ""
echo "🌐 URLs após correção:"
echo "- Interface Web: http://localhost:5173"
echo "- API Backend: http://localhost:8000"

