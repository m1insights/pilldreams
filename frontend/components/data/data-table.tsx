"use client"
/* eslint-disable @typescript-eslint/no-explicit-any */

import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronUp, ChevronDown, ChevronsUpDown, Download } from "lucide-react"

type SortDirection = "asc" | "desc" | null

interface Column<T> {
  key: keyof T | string
  label: string
  sortable?: boolean
  render?: (value: any, row: T) => React.ReactNode
  className?: string
  headerClassName?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  sortable?: boolean
  selectable?: boolean
  exportable?: boolean
  onRowClick?: (row: T) => void
  onExport?: (format: "csv" | "xlsx") => void
  emptyMessage?: string
  className?: string
  defaultSort?: { key: string; direction: SortDirection }
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  sortable = true,
  selectable = false,
  exportable = false,
  onRowClick,
  onExport,
  emptyMessage = "No data available",
  className,
  defaultSort,
}: DataTableProps<T>) {
  const [sortColumn, setSortColumn] = React.useState<string | null>(defaultSort?.key ?? null)
  const [sortDirection, setSortDirection] = React.useState<SortDirection>(defaultSort?.direction ?? null)
  const [selectedRows, setSelectedRows] = React.useState<Set<number>>(new Set())

  const handleSort = (columnKey: string) => {
    if (!sortable) return

    if (sortColumn === columnKey) {
      if (sortDirection === "asc") {
        setSortDirection("desc")
      } else if (sortDirection === "desc") {
        setSortColumn(null)
        setSortDirection(null)
      }
    } else {
      setSortColumn(columnKey)
      setSortDirection("asc")
    }
  }

  const sortedData = React.useMemo(() => {
    if (!sortColumn || !sortDirection) return data

    return [...data].sort((a, b) => {
      const aValue = a[sortColumn]
      const bValue = b[sortColumn]

      if (aValue === null || aValue === undefined) return 1
      if (bValue === null || bValue === undefined) return -1

      if (typeof aValue === "number" && typeof bValue === "number") {
        return sortDirection === "asc" ? aValue - bValue : bValue - aValue
      }

      const aStr = String(aValue).toLowerCase()
      const bStr = String(bValue).toLowerCase()
      return sortDirection === "asc"
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr)
    })
  }, [data, sortColumn, sortDirection])

  const toggleRowSelection = (index: number) => {
    const newSelected = new Set(selectedRows)
    if (newSelected.has(index)) {
      newSelected.delete(index)
    } else {
      newSelected.add(index)
    }
    setSelectedRows(newSelected)
  }

  const toggleAllRows = () => {
    if (selectedRows.size === data.length) {
      setSelectedRows(new Set())
    } else {
      setSelectedRows(new Set(data.map((_, i) => i)))
    }
  }

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) {
      return <ChevronsUpDown className="h-4 w-4 text-pd-text-muted" />
    }
    if (sortDirection === "asc") {
      return <ChevronUp className="h-4 w-4 text-pd-accent" />
    }
    return <ChevronDown className="h-4 w-4 text-pd-accent" />
  }

  const getValue = (row: T, key: string) => {
    // Support nested keys like "target.name"
    return key.split(".").reduce((obj, k) => obj?.[k], row as any)
  }

  return (
    <div className={cn("space-y-2", className)}>
      {/* Export button */}
      {exportable && onExport && (
        <div className="flex justify-end gap-2">
          <button
            onClick={() => onExport("csv")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-pd-text-secondary hover:text-pd-text-primary bg-pd-card border border-pd-border rounded-md hover:border-pd-accent/30 transition-colors"
          >
            <Download className="h-4 w-4" />
            CSV
          </button>
          <button
            onClick={() => onExport("xlsx")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-pd-text-secondary hover:text-pd-text-primary bg-pd-card border border-pd-border rounded-md hover:border-pd-accent/30 transition-colors"
          >
            <Download className="h-4 w-4" />
            Excel
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-pd-border bg-pd-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-pd-border bg-pd-secondary">
              {selectable && (
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedRows.size === data.length && data.length > 0}
                    onChange={toggleAllRows}
                    className="h-4 w-4 rounded border-pd-border bg-pd-card text-pd-accent focus:ring-pd-accent"
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={cn(
                    "px-4 py-3 text-left font-medium text-pd-text-secondary",
                    column.sortable !== false && sortable && "cursor-pointer select-none hover:text-pd-text-primary",
                    column.headerClassName
                  )}
                  onClick={() => column.sortable !== false && sortable && handleSort(String(column.key))}
                >
                  <div className="inline-flex items-center gap-1.5">
                    {column.label}
                    {column.sortable !== false && sortable && getSortIcon(String(column.key))}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  className="px-4 py-8 text-center text-pd-text-muted"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              sortedData.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={cn(
                    "border-b border-pd-border-subtle transition-colors",
                    onRowClick && "cursor-pointer",
                    selectedRows.has(rowIndex) && "bg-pd-accent/5",
                    "hover:bg-pd-hover"
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {selectable && (
                    <td className="w-10 px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedRows.has(rowIndex)}
                        onChange={() => toggleRowSelection(rowIndex)}
                        className="h-4 w-4 rounded border-pd-border bg-pd-card text-pd-accent focus:ring-pd-accent"
                      />
                    </td>
                  )}
                  {columns.map((column) => {
                    const value = getValue(row, String(column.key))
                    return (
                      <td
                        key={String(column.key)}
                        className={cn("px-4 py-3 text-pd-text-primary", column.className)}
                      >
                        {column.render ? column.render(value, row) : value}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Selection count */}
      {selectable && selectedRows.size > 0 && (
        <div className="text-sm text-pd-text-secondary">
          {selectedRows.size} row{selectedRows.size !== 1 ? "s" : ""} selected
        </div>
      )}
    </div>
  )
}
