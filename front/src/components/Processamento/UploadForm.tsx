import React from "react";
// Exemplo (Assumindo que você usa componentes de Input)
import { Input } from "@/components/ui/input";

// --- 1. INTERFACE CORRIGIDA: ATUALIZADA PARA MATCH COM PROCESSAR.TSX ---
interface UploadFormProps {
  // O handler agora se chama onFileSelect e passa o File
  onFileSelect: (file: File) => void;
  // Adicionamos a prop 'disabled' para evitar uploads enquanto processa
  disabled: boolean;
}

// --- 2. COMPONENTE ATUALIZADO: DESESTRUTURANDO AS PROPS CORRETAS ---
const UploadForm = ({ onFileSelect, disabled }: UploadFormProps) => {
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      // Chama o handler pai com o objeto File (e não com URL de preview, que é criado no pai)
      onFileSelect(file);

      // Limpa o valor do input para permitir o upload do mesmo arquivo novamente
      event.target.value = "";
    }
  };

  return (
    <div className="p-6 border rounded-lg shadow-sm bg-card">
      <h3 className="text-lg font-semibold mb-3 text-foreground">
        Selecionar Imagem
      </h3>
      <Input
        id="image-upload"
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        disabled={disabled} // <<< USANDO A PROP DISABLED
      />
      <p className="text-sm text-muted-foreground mt-2">
        Formatos suportados: PNG, JPG.
      </p>
    </div>
  );
};

export default UploadForm;
