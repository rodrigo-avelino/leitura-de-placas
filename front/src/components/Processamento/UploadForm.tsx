// Exemplo (Assumindo que você usa componentes de Input)
import { Input } from "@/components/ui/input";

interface UploadFormProps {
  onImageUpload: (file: File) => void;
}

const UploadForm = ({ onImageUpload }: UploadFormProps) => {
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      onImageUpload(file);
    }
  };

  return (
    <div className="p-6 border rounded-lg shadow-sm bg-card">
           {" "}
      <h3 className="text-lg font-semibold mb-3 text-foreground">
        Selecionar Imagem
      </h3>
           {" "}
      <Input
        id="image-upload"
        type="file"
        accept="image/*"
        onChange={handleFileChange}
      />
           {" "}
      <p className="text-sm text-muted-foreground mt-2">
        Formatos suportados: PNG, JPG.
      </p>
         {" "}
    </div>
  );
};

export default UploadForm;
