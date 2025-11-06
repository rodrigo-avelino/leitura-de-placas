import { useState, useMemo } from "react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Eye, Trash2, Calendar, Clock, Car, Loader2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

// --- TIPAGENS CORRIGIDAS E COMPLETAS ---
type DeleteStatus = "idle" | "running" | "success" | "failed";

export interface Registro {
  // Aceita string (WS) ou number (DB)
  id: number | string;
  placa: string;
  dataHora: string;
  imagemUrl: string;
  tipo_placa?: string; // Incluído
}

interface TabelaRegistrosProps {
  registros: Registro[];
  // Corrigido para aceitar id: number | string
  onDelete: (id: number | string) => void;
  // Adicionado o status de deleção do hook
  deleteStatus: DeleteStatus;
}

const TabelaRegistros = ({
  registros,
  onDelete,
  deleteStatus,
}: TabelaRegistrosProps) => {
  const [selectedRegistro, setSelectedRegistro] = useState<Registro | null>(
    null
  );
  const [registroToDelete, setRegistroToDelete] = useState<Registro | null>(
    null
  );

  // Lógica para mostrar feedback visual do status de deleção
  useMemo(() => {
    if (deleteStatus === "success") {
      toast.success("Registro removido com sucesso.");
      toast.dismiss(`delete-progress`);
    } else if (deleteStatus === "failed") {
      toast.error("Falha ao remover registro. Tente novamente.");
      toast.dismiss(`delete-progress`);
    }
  }, [deleteStatus]);

  const handleDeleteClick = (registro: Registro) => {
    setRegistroToDelete(registro);
  };

  const confirmDelete = () => {
    if (!registroToDelete) return;
    
    // Mostra o feedback de carregamento
    toast.loading(`Removendo registro da placa ${registroToDelete.placa}...`, {
      id: `delete-progress`,
    });
    
    // Chama o handler do componente pai (que executa o deleteRegistro(id) do hook)
    onDelete(registroToDelete.id);
    
    // Fecha o modal
    setRegistroToDelete(null);
  };

  const cancelDelete = () => {
    setRegistroToDelete(null);
  };

  // Helper para exibir o Badge de tipo de placa
  const renderTipoPlaca = (tipo?: string) => {
    if (!tipo) return null;
    const variant = tipo === "MERCOSUL" ? "default" : "secondary";
    return <Badge variant={variant}>{tipo}</Badge>;
  };

  // Helper para verificar se o ID é válido (não é null, undefined, ou string vazia)
  const isIdValid = (id: number | string | undefined | null) =>
    !!id && id !== "undefined";

  // Verifica se a deleção está em andamento.
  const isDeleting = deleteStatus === "running";

  return (
    <>
      {registros.length === 0 ? (
        <Card className="p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Car className="w-8 h-8 text-muted-foreground" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-1">
                Nenhum registro encontrado
              </h3>
              <p className="text-sm text-muted-foreground">
                Tente ajustar os filtros ou adicione novos registros
              </p>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {registros.map((registro) => (
            <Card
              // O key é o único lugar onde um ID inválido pode ser problemático se for null, mas o React trata isso.
              key={registro.id}
              className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer"
              onClick={() => setSelectedRegistro(registro)}
            >
              <CardContent className="p-6 space-y-3">
                {/* Header com ID e Placa */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-accent/10">
                      <Car className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Placa</p>
                      <p className="font-mono font-bold text-xl text-foreground">
                        {registro.placa}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {renderTipoPlaca(registro.tipo_placa)}
                    <Badge className="font-mono">
                      {/* CORREÇÃO APLICADA AQUI: Garante que um valor seja renderizado */}
                      {isIdValid(registro.id) ? `#${registro.id}` : "#?"}
                    </Badge>
                  </div>
                </div>

                <Separator />

                {/* Data e Hora */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-primary" />
                    <div>
                      <p className="text-xs text-muted-foreground">Data</p>
                      <p className="font-medium text-foreground">
                        {format(new Date(registro.dataHora), "dd/MM/yy", {
                          locale: ptBR,
                        })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-success" />
                    <div>
                      <p className="text-xs text-muted-foreground">Horário</p>
                      <p className="font-medium text-foreground">
                        {format(new Date(registro.dataHora), "HH:mm", {
                          locale: ptBR,
                        })}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Ações */}
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedRegistro(registro);
                    }}
                    disabled={isDeleting || !isIdValid(registro.id)} // Desabilita se ID inválido
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Ver Detalhes
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    // Desabilita durante o processamento de deleção OU se o ID for inválido
                    disabled={isDeleting || !isIdValid(registro.id)}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteClick(registro);
                    }}
                  >
                    {isDeleting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Diálogo de Detalhes */}
      <Dialog
        open={!!selectedRegistro}
        onOpenChange={() => setSelectedRegistro(null)}
      >
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Detalhes do Registro</DialogTitle>
            <DialogDescription>
              Informações completas do veículo detectado
            </DialogDescription>
          </DialogHeader>

          {selectedRegistro && (
            <div className="space-y-6">
              {/* Informações do Registro */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Placa */}
                <Card className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-accent/10">
                      <Car className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Placa</p>
                      <p className="text-lg font-mono font-bold text-foreground">
                        {selectedRegistro.placa}
                      </p>
                    </div>
                  </div>
                </Card>
                {/* Data */}
                <Card className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Calendar className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Data</p>
                      <p className="text-lg font-semibold text-foreground">
                        {format(
                          new Date(selectedRegistro.dataHora),
                          "dd/MM/yyyy",
                          { locale: ptBR }
                        )}
                      </p>
                    </div>
                  </div>
                </Card>
                {/* Horário */}
                <Card className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-success/10">
                      <Clock className="w-5 h-5 text-success" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Horário</p>
                      <p className="text-lg font-semibold text-foreground">
                        {format(
                          new Date(selectedRegistro.dataHora),
                          "HH:mm:ss",
                          { locale: ptBR }
                        )}
                      </p>
                    </div>
                  </div>
                </Card>
              </div>

              <Separator />

              {/* Imagem do Veículo */}
              <div>
                <h4 className="text-sm font-semibold text-foreground mb-3">
                  Imagem Capturada (Recorte)
                </h4>
                <div className="rounded-lg overflow-hidden border border-border bg-muted">
                  <img
                    src={selectedRegistro.imagemUrl}
                    alt={`Veículo placa ${selectedRegistro.placa}`}
                    className="w-full h-auto"
                  />
                </div>
              </div>

              {/* ID do Registro e Tipo de Placa */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted">
                <span className="text-sm text-muted-foreground">
                  Tipo de Placa:
                  <Badge
                    className="ml-2"
                    variant={
                      selectedRegistro.tipo_placa === "MERCOSUL"
                        ? "default"
                        : "secondary"
                    }
                  >
                    {selectedRegistro.tipo_placa || "INDEFINIDO"}
                  </Badge>
                </span>
                <span className="font-mono font-semibold text-foreground">
                  {/* CORREÇÃO APLICADA AQUI: Exibe o ID válido ou 'ID INVÁLIDO' */}
                  {isIdValid(selectedRegistro.id)
                    ? `#${selectedRegistro.id}`
                    : "ID INVÁLIDO"}
                </span>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de Confirmação de Exclusão */}
      <AlertDialog open={!!registroToDelete} onOpenChange={(open) => !open && cancelDelete()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-full bg-destructive/10">
                <AlertTriangle className="w-6 h-6 text-destructive" />
              </div>
              <AlertDialogTitle className="text-xl">
                Confirmar Exclusão
              </AlertDialogTitle>
            </div>
            <AlertDialogDescription className="text-base space-y-3 pt-2">
              <p>
                Tem certeza que deseja excluir o registro da placa{" "}
                <span className="font-mono font-bold text-foreground">
                  {registroToDelete?.placa}
                </span>
                ?
              </p>
              <p className="text-sm text-muted-foreground">
                Esta ação não pode ser desfeita. O registro será permanentemente removido do banco de dados.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 sm:gap-2">
            <AlertDialogCancel onClick={cancelDelete} disabled={isDeleting}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              disabled={isDeleting}
              className="bg-destructive hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Excluindo...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Excluir Registro
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default TabelaRegistros;
