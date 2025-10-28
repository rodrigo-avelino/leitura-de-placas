import { Card } from "@/components/ui/card";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ImageDisplayProps {
  imageUrl: string;
  croppedPlate: string | null;
  onClear: () => void;
}

const ImageDisplay = ({ imageUrl, croppedPlate, onClear }: ImageDisplayProps) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Imagem Original</h3>
        <Button variant="ghost" size="icon" onClick={onClear}>
          <X className="w-4 h-4" />
        </Button>
      </div>
      
      <div className="rounded-lg overflow-hidden border border-border mb-6">
        <img
          src={imageUrl}
          alt="Veículo"
          className="w-full h-auto"
        />
      </div>

      {croppedPlate && (
        <>
          <h3 className="text-lg font-semibold text-foreground mb-4">Recorte da Placa</h3>
          <div className="rounded-lg overflow-hidden border border-border bg-muted p-4 flex items-center justify-center">
            <img
              src={croppedPlate}
              alt="Placa recortada"
              className="max-w-full h-auto"
            />
          </div>
        </>
      )}
    </Card>
  );
};

export default ImageDisplay;
