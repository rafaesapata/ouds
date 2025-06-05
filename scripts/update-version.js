#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Ler a versão atual do package.json
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const newVersion = packageJson.version;

console.log(`🔄 Atualizando versão para ${newVersion}...`);

// Arquivos para atualizar
const filesToUpdate = [
  {
    file: 'ouds-frontend/.env.example',
    pattern: /OUDS_VERSION=.*/,
    replacement: `OUDS_VERSION=${newVersion}`
  },
  {
    file: 'ouds-frontend/.env',
    pattern: /OUDS_VERSION=.*/,
    replacement: `OUDS_VERSION=${newVersion}`,
    optional: true
  },
  {
    file: 'ouds_config.json',
    pattern: /"version": ".*"/,
    replacement: `"version": "${newVersion}"`
  },
  {
    file: 'README.md',
    pattern: /OUDS - Oráculo UDS v\d+\.\d+\.\d+/g,
    replacement: `OUDS - Oráculo UDS v${newVersion}`
  },
  {
    file: 'OUDS_GUIA_RAPIDO.md',
    pattern: /OUDS v\d+\.\d+\.\d+/g,
    replacement: `OUDS v${newVersion}`
  }
];

// Atualizar cada arquivo
filesToUpdate.forEach(({ file, pattern, replacement, optional }) => {
  try {
    if (!fs.existsSync(file)) {
      if (optional) {
        console.log(`⏭️ Arquivo opcional ${file} não encontrado, pulando...`);
        return;
      } else {
        console.log(`⚠️ Arquivo ${file} não encontrado!`);
        return;
      }
    }

    let content = fs.readFileSync(file, 'utf8');
    const originalContent = content;
    
    content = content.replace(pattern, replacement);
    
    if (content !== originalContent) {
      fs.writeFileSync(file, content, 'utf8');
      console.log(`✅ Atualizado: ${file}`);
    } else {
      console.log(`ℹ️ Nenhuma alteração necessária: ${file}`);
    }
  } catch (error) {
    console.log(`❌ Erro ao atualizar ${file}: ${error.message}`);
  }
});

// Atualizar install_ouds.sh
try {
  const installScript = fs.readFileSync('install_ouds.sh', 'utf8');
  const updatedScript = installScript.replace(
    /"version": ".*"/,
    `"version": "${newVersion}"`
  );
  
  if (updatedScript !== installScript) {
    fs.writeFileSync('install_ouds.sh', updatedScript, 'utf8');
    console.log('✅ Atualizado: install_ouds.sh');
  }
} catch (error) {
  console.log(`❌ Erro ao atualizar install_ouds.sh: ${error.message}`);
}

console.log(`🎉 Versão atualizada para ${newVersion} em todos os arquivos!`);
console.log('📝 Lembre-se de fazer commit das alterações.');

