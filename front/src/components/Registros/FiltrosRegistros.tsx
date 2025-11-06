// components/Registros/FiltrosRegistros.tsx (CORRIGIDO)

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, X, Calendar, Filter } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface FiltrosRegistrosProps {
  // Mantemos o onFilter principal, mas ele será chamado com diferentes focos
  onFilter: (filters: {
    placa: string;
    dataInicio: string;
    dataFim: string;
  }) => void;
}

const FiltrosRegistros = ({ onFilter }: FiltrosRegistrosProps) => {
  const [placa, setPlaca] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [isPopoverOpen, setIsPopoverOpen] = useState(false); // Novo estado para controlar o Popover

  // --- FUNÇÃO 1: Ação de Pesquisar (Aplica apenas o filtro de placa) ---
  const handleSearchByPlate = () => {
    // Aplica o filtro de placa, mantendo as datas existentes
    onFilter({ placa, dataInicio, dataFim });
  };

  // --- FUNÇÃO 2: Ação de Aplicar Filtro de Período ---
  const handleApplyPeriodFilter = () => {
    // Aplica a placa existente E as novas datas
    onFilter({ placa, dataInicio, dataFim });
    setIsPopoverOpen(false); // Fecha o Popover
  };

  const clearFilters = () => {
    setPlaca("");
    setDataInicio("");
    setDataFim("");
    onFilter({ placa: "", dataInicio: "", dataFim: "" });
  };

  // Conta filtros ativos (placa + datas)
  const activeFiltersCount = [placa, dataInicio, dataFim].filter(
    Boolean
  ).length;

  return (
    <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      {/* 1. Search Bar Principal */}
      <div className="relative flex-1 w-full sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          placeholder="Buscar por placa (ex: ABC-1234)..."
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleSearchByPlate()} // Enter aciona Pesquisar
          className="pl-10 h-12 text-base bg-card border-2 focus-visible:ring-2"
        />
      </div>

      {/* 2. Botão Pesquisar (Aplicar Placa) */}
      <Button onClick={handleSearchByPlate} className="h-12 px-6">
        <Search className="w-4 h-4 mr-2" />
        Pesquisar
      </Button>

      {/* 3. Filtro de Datas - Popover */}
      <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
        <PopoverTrigger asChild>
          {/* Botão que agora é chamado 'Filtrar' */}
          <Button variant="outline" className="h-12 gap-2 relative">
            <Filter className="w-4 h-4" />
            <span className="hidden sm:inline">Filtrar (Período)</span>
            {(dataInicio || dataFim) && (
              <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-xs">
                {/* Exibe o número de filtros de data ativos (1 ou 2) */}
                {[dataInicio, dataFim].filter(Boolean).length}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>

        <PopoverContent className="w-80" align="end">
          <div className="space-y-4">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Seleção de Período
            </h4>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">
                  Data Inicial
                </label>
                <Input
                  type="date"
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">
                  Data Final
                </label>
                <Input
                  type="date"
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                />
              </div>
            </div>

            {/* NOVO: Botão Aplicar que fecha o Popover */}
            <Button onClick={handleApplyPeriodFilter} className="w-full">
              Aplicar Filtro de Data
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      {/* 4. Limpar Filtros */}
      {activeFiltersCount > 0 && (
        <Button
          variant="ghost"
          onClick={clearFilters}
          className="h-12 text-muted-foreground hover:text-foreground"
        >
          <X className="w-4 h-4 mr-2" />
          Limpar
        </Button>
      )}
    </div>
  );
};

export default FiltrosRegistros;
