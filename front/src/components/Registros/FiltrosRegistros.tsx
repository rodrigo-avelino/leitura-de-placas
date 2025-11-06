// components/Registros/FiltrosRegistros.tsx (CORRIGIDO + FILTRO DE TIPO)

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, X, Calendar, Filter, Car, IdCard  } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface FiltrosRegistrosProps {
  // Adicionado o filtro de tipo de placa
  onFilter: (filters: {
    placa: string;
    dataInicio: string;
    dataFim: string;
    tipoPlaca: string; // Novo filtro: "TODOS", "MERCOSUL", "ANTIGA"
  }) => void;
}

const FiltrosRegistros = ({ onFilter }: FiltrosRegistrosProps) => {
  const [placa, setPlaca] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [tipoPlaca, setTipoPlaca] = useState("TODOS"); // Novo estado
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  // --- FUNÇÃO 1: Ação de Pesquisar (Aplica apenas o filtro de placa) ---
  const handleSearchByPlate = () => {
    // Aplica o filtro de placa, mantendo as datas e tipo existentes
    onFilter({ placa, dataInicio, dataFim, tipoPlaca });
  };

  // --- FUNÇÃO 2: Ação de Aplicar Filtro de Período ---
  const handleApplyPeriodFilter = () => {
    // Aplica a placa existente, tipo de placa E as novas datas
    onFilter({ placa, dataInicio, dataFim, tipoPlaca });
    setIsPopoverOpen(false); // Fecha o Popover
  };

  const clearFilters = () => {
    setPlaca("");
    setDataInicio("");
    setDataFim("");
    setTipoPlaca("TODOS");
    onFilter({ placa: "", dataInicio: "", dataFim: "", tipoPlaca: "TODOS" });
  };

  // Conta filtros ativos (placa + datas + tipo)
  const activeFiltersCount = [
    placa, 
    dataInicio, 
    dataFim, 
    tipoPlaca !== "TODOS" ? tipoPlaca : ""
  ].filter(Boolean).length;

  return (
    <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      {/* 1. Search Bar Principal */}
      <div className="relative flex-1 w-full sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          placeholder="Buscar por placa (ex: ABC-1234)..."
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleSearchByPlate()}
          className="pl-10 h-12 text-base bg-card border-2 focus-visible:ring-2"
        />
      </div>

      {/* 2. Botão Pesquisar */}
      <Button onClick={handleSearchByPlate} className="h-12 px-6">
        <Search className="w-4 h-4 mr-2" />
        Pesquisar
      </Button>

      {/* 3. Filtros Avançados (Tipo + Período) - Popover */}
      <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="h-12 gap-2 relative">
            <Filter className="w-4 h-4" />
            <span className="hidden sm:inline">Filtros</span>
            {(dataInicio || dataFim || tipoPlaca !== "TODOS") && (
              <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-xs">
                {[dataInicio, dataFim, tipoPlaca !== "TODOS" ? tipoPlaca : ""].filter(Boolean).length}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>

        <PopoverContent className="w-80" align="end">
          <div className="space-y-5">
            <h4 className="font-semibold text-base flex items-center gap-2">
              <Filter className="w-4 h-4" />
              Filtros Avançados
            </h4>

            {/* Filtro de Tipo de Placa */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground font-medium flex items-center gap-2">
                <IdCard className="w-3.5 h-3.5" />
                Tipo de Placa
              </label>
              <Select value={tipoPlaca} onValueChange={setTipoPlaca}>
                <SelectTrigger className="h-10">
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="TODOS">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-muted-foreground" />
                      Todas
                    </div>
                  </SelectItem>
                  <SelectItem value="MERCOSUL">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-500" />
                      Mercosul
                    </div>
                  </SelectItem>
                  <SelectItem value="ANTIGA">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-orange-500" />
                      Antiga
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Filtro de Período */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground font-medium flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5" />
                Período
              </label>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">
                    Data Inicial
                  </label>
                  <Input
                    type="date"
                    value={dataInicio}
                    onChange={(e) => setDataInicio(e.target.value)}
                    className="h-10"
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
                    className="h-10"
                  />
                </div>
              </div>
            </div>

            {/* Botão Aplicar Filtros */}
            <Button onClick={handleApplyPeriodFilter} className="w-full">
              <Filter className="w-4 h-4 mr-2" />
              Aplicar Filtros
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
