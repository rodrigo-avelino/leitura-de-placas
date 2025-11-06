import React, { useState, useRef } from "react";
import { Upload, Image as ImageIcon, FileImage, X, Play, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface UploadFormProps {
  onFileSelect: (file: File) => void;
  disabled: boolean;
  uploadedImageUrl?: string | null;
  onProcess?: () => void;
  onClear?: () => void;
  isProcessing?: boolean;
  finalResult?: {
    status: "ok" | "fail" | "error";
    texto_final: string | null;
  } | null;
  croppedPlate?: string | null;
  binarizedImage?: string | null;
  segmentedImage?: string | null;
}

const UploadForm = ({ 
  onFileSelect, 
  disabled, 
  uploadedImageUrl,
  onProcess,
  onClear,
  isProcessing = false,
  finalResult,
  croppedPlate,
  binarizedImage,
  segmentedImage
}: UploadFormProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && isValidImageFile(file)) {
      onFileSelect(file);
      event.target.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !uploadedImageUrl) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled || uploadedImageUrl) return;

    const file = e.dataTransfer.files?.[0];
    if (file && isValidImageFile(file)) {
      onFileSelect(file);
    }
  };

  const isValidImageFile = (file: File) => {
    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    return validTypes.includes(file.type);
  };

  const handleButtonClick = () => {
    if (!uploadedImageUrl) {
      fileInputRef.current?.click();
    }
  };

  // Estado: Mostrar preview da imagem
  if (uploadedImageUrl) {
    return (
      <div className="overflow-hidden transition-all duration-300">
        <div className="relative">
          {/* Imagem Preview */}
          <div className="relative aspect-video bg-black/5 rounded-lg overflow-hidden border-2 border-border">
            <img
              src={uploadedImageUrl}
              alt="Imagem carregada"
              className="w-full h-full object-contain"
            />
            
            {/* Overlay de processamento */}
            {isProcessing && (
              <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center">
                <div className="text-center space-y-3">
                  <Loader2 className="w-12 h-12 text-white animate-spin mx-auto" />
                  <p className="text-white font-medium">Processando imagem...</p>
                </div>
              </div>
            )}

            {/* Badge de status no canto superior direito */}
            {finalResult && (
              <div className="absolute top-4 right-4">
                <Badge
                  variant={finalResult.status === "ok" ? "default" : "destructive"}
                  className="text-sm px-3 py-1 shadow-lg"
                >
                  {finalResult.status === "ok" ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 mr-1" />
                      Sucesso
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4 mr-1" />
                      Falha
                    </>
                  )}
                </Badge>
              </div>
            )}
          </div>

          {/* Resultado da Placa */}
          {finalResult?.texto_final && (
            <div className={`p-6 text-center border-t-2 ${
              finalResult.status === "ok" 
                ? "bg-green-50 dark:bg-green-950/20 border-green-500" 
                : "bg-red-50 dark:bg-red-950/20 border-red-500"
            }`}>
              <p className="text-sm text-muted-foreground mb-2">Placa Detectada</p>
              <p className="text-4xl font-bold tracking-wider font-mono">
                {finalResult.texto_final}
              </p>
            </div>
          )}

          {/* Miniaturas das etapas de processamento */}
          {(croppedPlate || binarizedImage || segmentedImage) && (
            <div className="p-4 bg-muted/30 border-t">
              <p className="text-xs text-muted-foreground mb-3 font-medium">Etapas do Processamento</p>
              <div className="grid grid-cols-3 gap-3">
                {croppedPlate && (
                  <div className="space-y-1">
                    <div className="aspect-video bg-black rounded-md overflow-hidden border">
                      <img
                        src={croppedPlate}
                        alt="Placa recortada"
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <p className="text-xs text-center text-muted-foreground">Recorte</p>
                  </div>
                )}
                {binarizedImage && (
                  <div className="space-y-1">
                    <div className="aspect-video bg-black rounded-md overflow-hidden border">
                      <img
                        src={binarizedImage}
                        alt="Imagem binarizada"
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <p className="text-xs text-center text-muted-foreground">Binarização</p>
                  </div>
                )}
                {segmentedImage && (
                  <div className="space-y-1">
                    <div className="aspect-video bg-black rounded-md overflow-hidden border">
                      <img
                        src={segmentedImage}
                        alt="Imagem segmentada"
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <p className="text-xs text-center text-muted-foreground">Segmentação</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Ações */}
          <div className="p-4 bg-card flex gap-3">
            <Button
              onClick={onClear}
              variant="outline"
              disabled={isProcessing}
              className="flex-1"
            >
              <X className="w-4 h-4 mr-2" />
              Limpar
            </Button>
            
            {!finalResult && (
              <Button
                onClick={onProcess}
                disabled={isProcessing}
                className="flex-1"
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processando...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Processar Imagem
                  </>
                )}
              </Button>
            )}

            {finalResult && (
              <Button
                onClick={() => {
                  fileInputRef.current?.click();
                }}
                variant="default"
                className="flex-1"
              >
                <Upload className="w-4 h-4 mr-2" />
                Nova Imagem
              </Button>
            )}
          </div>
        </div>

        {/* Input file oculto */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/webp"
          onChange={handleFileChange}
          disabled={disabled}
          className="hidden"
        />
      </div>
    );
  }

  // Estado: Mostrar área de upload
  return (
    <div className="overflow-hidden">
      <div
        className={`
          relative p-12 transition-all duration-300 ease-in-out cursor-pointer rounded-lg border-2 border-dashed
          ${isDragging ? "bg-primary/10 border-primary scale-[0.98]" : "bg-gradient-to-br from-background to-muted/20 border-border hover:border-primary/50"}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={!disabled ? handleButtonClick : undefined}
      >
        {/* Input file oculto */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/webp"
          onChange={handleFileChange}
          disabled={disabled}
          className="hidden"
        />

        {/* Área de upload visual */}
        <div className="flex flex-col items-center justify-center space-y-6">
          {/* Ícone animado */}
          <div
            className={`
              relative p-8 rounded-full bg-primary/10 transition-all duration-300
              ${isDragging ? "scale-110 bg-primary/20" : "scale-100 hover:scale-105"}
            `}
          >
            <Upload
              className={`
                w-16 h-16 text-primary transition-transform duration-300
                ${isDragging ? "animate-bounce" : ""}
              `}
            />
            <div
              className={`
                absolute inset-0 rounded-full bg-primary/20 blur-xl
                ${isDragging ? "opacity-100 scale-110" : "opacity-0 scale-100"}
                transition-all duration-300
              `}
            />
          </div>

          {/* Texto principal */}
          <div className="text-center space-y-3">
            <h3 className="text-2xl font-bold text-foreground">
              {isDragging ? "Solte a imagem aqui" : "Enviar Imagem da Placa"}
            </h3>
            <p className="text-sm text-muted-foreground max-w-md">
              {isDragging
                ? "Solte o arquivo para fazer upload"
                : "Arraste e solte uma imagem aqui ou clique para selecionar do seu dispositivo"}
            </p>
          </div>

          {/* Botão de ação */}
          <Button
            variant="default"
            size="lg"
            disabled={disabled}
            className="mt-2 group relative overflow-hidden px-8 py-6 text-base"
            onClick={(e) => {
              e.stopPropagation();
              handleButtonClick();
            }}
          >
            <FileImage className="w-5 h-5 mr-2" />
            Selecionar Arquivo
          </Button>

          {/* Informações de formato */}
          <div className="flex items-center gap-2 pt-6 border-t border-border/50 w-full justify-center">
            <ImageIcon className="w-4 h-4 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              Formatos aceitos: <span className="font-semibold">JPG, PNG, WEBP</span>
            </p>
          </div>
        </div>

        {/* Overlay de drag */}
        {isDragging && (
          <div className="absolute inset-0 border-4 border-dashed border-primary rounded-lg pointer-events-none animate-pulse" />
        )}
      </div>
    </div>
  );
};

export default UploadForm;
