import { useState } from "react";
import { Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface UploadFormProps {
  onImageUpload: (imageUrl: string) => void;
}

const UploadForm = ({ onImageUpload }: UploadFormProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          onImageUpload(e.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          onImageUpload(e.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">Upload de Imagem</h3>
      
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging ? "border-accent bg-accent/5" : "border-border"}
        `}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <p className="text-sm text-muted-foreground mb-4">
          Arraste uma imagem aqui ou clique para selecionar
        </p>
        
        <input
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload">
          <Button asChild>
            <span>Selecionar Imagem</span>
          </Button>
        </label>
      </div>
    </Card>
  );
};

export default UploadForm;
