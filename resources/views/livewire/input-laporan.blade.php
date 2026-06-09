<div class="space-y-3">

    {{-- ── Flash messages ─────────────────────────────────────────── --}}
    @if($successMessage)
    <div class="bg-green-50 border border-green-200 text-green-700 text-xs px-4 py-2 rounded flex items-center justify-between">
        <span>✓ {{ $successMessage }}</span>
        <button wire:click="$set('successMessage', null)" class="text-green-500 hover:text-green-700 ml-4">✕</button>
    </div>
    @endif
    @if($errorMessage)
    <div class="bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-2 rounded flex items-center justify-between">
        <span>{{ $errorMessage }}</span>
        <button wire:click="$set('errorMessage', null)" class="text-red-400 hover:text-red-600 ml-4">✕</button>
    </div>
    @endif

    {{-- ── Balance Warning (v2-style confirm) ─────────────────────── --}}
    @if($balanceWarning)
    <div class="bg-yellow-50 border border-yellow-300 text-xs px-4 py-3 rounded flex items-center justify-between gap-4">
        <div class="flex items-center gap-2">
            <span class="text-yellow-700 font-bold">⚠ Balance Tidak Nol</span>
            <span class="text-yellow-600">
                BALANCE = <strong class="font-mono">{{ number_format($calcBalance, 4) }}</strong>
                — Data belum balance. Tetap simpan?
            </span>
        </div>
        <div class="flex gap-2 flex-shrink-0">
            <button wire:click="forceSave"
                class="px-3 py-1 text-xs font-medium text-white bg-yellow-500 rounded hover:bg-yellow-600 cursor-pointer">
                Ya, Tetap Simpan
            </button>
            <button wire:click="cancelSave"
                class="px-3 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">
                Batal
            </button>
        </div>
    </div>
    @endif

    {{-- ── Header bar ──────────────────────────────────────────────── --}}
    <div class="bg-white border border-gray-200 rounded" style="border-top: 2px solid #dc2626;">
        <div class="flex flex-wrap items-center gap-3 px-4 py-2">

            {{-- Shop / Section --}}
            <div class="flex items-center gap-1.5">
                <span class="text-xs text-gray-500">Shop</span>
                @if(!empty($sections))
                <select wire:model.live="shop"
                    class="border border-gray-300 rounded px-2 py-1 text-xs w-36 focus:outline-none focus:border-red-400 bg-white cursor-pointer">
                    <option value="">— pilih section —</option>
                    @foreach($sections as $sec)
                    <option value="{{ $sec['name'] }}">{{ $sec['name'] }}</option>
                    @endforeach
                </select>
                @else
                <input wire:model.lazy="shop" type="text" placeholder="Section"
                    class="border border-gray-300 rounded px-2 py-1 text-xs w-32 focus:outline-none focus:border-red-400">
                @endif
            </div>

            <div class="w-px h-5 bg-gray-200"></div>

            {{-- Date with navigation --}}
            <div class="flex items-center gap-1">
                <span class="text-xs text-gray-500 mr-0.5">Date</span>
                <button wire:click="prevDate"
                    class="w-6 h-6 flex items-center justify-center border border-gray-300 rounded text-xs text-gray-500 bg-white hover:bg-gray-50 cursor-pointer">
                    &lt;
                </button>
                <input wire:model="date" type="date"
                    class="border border-gray-300 rounded px-2 py-1 text-xs w-32 focus:outline-none focus:border-red-400">
                <button wire:click="nextDate"
                    class="w-6 h-6 flex items-center justify-center border border-gray-300 rounded text-xs text-gray-500 bg-white hover:bg-gray-50 cursor-pointer">
                    &gt;
                </button>
                <span class="text-xs font-bold text-red-600 w-12 text-center">{{ $dayName }}</span>
            </div>

            <div class="w-px h-5 bg-gray-200"></div>

            {{-- Shift (dropdown from master) --}}
            <div class="flex items-center gap-1.5">
                <span class="text-xs text-gray-500">Shift</span>
                <select wire:model.live="shift"
                    class="border border-gray-300 rounded px-2 py-1 text-xs w-28 focus:outline-none focus:border-red-400 bg-white cursor-pointer">
                    @foreach($shifts as $s)
                    <option value="{{ $s['name'] }}">{{ $s['name'] }}</option>
                    @endforeach
                </select>
            </div>

            <div class="w-px h-5 bg-gray-200"></div>

            {{-- Hour (READ-ONLY — computed from shift + OT + Jumat logic) --}}
            <div class="flex items-center gap-1.5">
                <span class="text-xs text-gray-500">Hour</span>
                <span class="border border-gray-200 bg-gray-50 rounded px-2 py-1 text-xs w-14 font-bold font-mono text-center text-gray-700 select-none inline-block">
                    {{ number_format($calcTotal, 2) }}
                </span>
            </div>

            {{-- OT (dropdown) --}}
            <div class="flex items-center gap-1.5">
                <span class="text-xs text-gray-500">OT</span>
                <select wire:model.live="ot"
                    class="border border-gray-300 rounded px-2 py-1 text-xs w-16 text-center focus:outline-none focus:border-red-400 bg-white cursor-pointer">
                    <option>—</option>
                    <option>2H</option>
                    <option>3H</option>
                    <option>11H</option>
                </select>
            </div>

            <div class="w-px h-5 bg-gray-200"></div>

            {{-- Hari Pengganti --}}
            <div class="flex items-center gap-1.5">
                <input wire:model.live="hariPengganti" type="checkbox"
                    class="border border-gray-300 rounded text-red-600 cursor-pointer">
                <span class="text-xs text-gray-600">Hari Pengganti</span>
                @if($hariPengganti)
                <select wire:model.live="hariPenggantiDay"
                    class="border border-gray-300 rounded px-2 py-1 text-xs w-20 focus:outline-none focus:border-red-400 bg-yellow-50 cursor-pointer">
                    @foreach(['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu'] as $hari)
                    <option>{{ $hari }}</option>
                    @endforeach
                </select>
                @endif
            </div>

            {{-- Username (far right) --}}
            <div class="ml-auto text-xs font-bold text-red-600 uppercase tracking-wide">
                {{ auth()->user()?->name ?? 'USER' }}
            </div>
        </div>
    </div>

    {{-- ── Three panels: Production Volume | Absence | Calculation Hour ── --}}
    <div class="flex gap-3 items-start">

        {{-- ── Production Volume ─────────────────────────────────────── --}}
        <div class="flex-1 min-w-0 bg-white border border-gray-300 rounded-sm">
            <div class="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-b border-gray-200">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700">Production Volume</span>
                <div class="flex gap-1">
                    <button wire:click="addProductionRow"
                        class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-green-50 text-green-700 border border-green-300 rounded-sm cursor-pointer">+ Add</button>
                    <button wire:click="removeLastProductionRow"
                        class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-red-50 text-red-600 border border-red-300 rounded-sm cursor-pointer">× Del</button>
                </div>
            </div>
            <table class="w-full text-xs">
                <thead>
                    <tr class="bg-gray-100 border-b border-gray-200">
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Model</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-16">Plan QTY</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-16">Act QTY</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-20">Plan H</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-20">Act H</th>
                    </tr>
                </thead>
                <tbody>
                    @foreach($productions as $i => $row)
                    <tr wire:key="prod-{{ $i }}" class="border-b border-gray-100">
                        <td class="p-px">
                            @if(!empty($shopModels))
                            <select wire:model.live="productions.{{ $i }}.model"
                                class="w-full px-2 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                @foreach($shopModels as $sm)
                                <option value="{{ $sm['name'] }}">{{ $sm['name'] }}</option>
                                @endforeach
                            </select>
                            @else
                            <input wire:model.live="productions.{{ $i }}.model" type="text"
                                class="w-full px-2 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"
                                placeholder="pilih section dahulu">
                            @endif
                        </td>
                        <td class="p-px">
                            {{-- lazy → auto-fill Plan H on blur --}}
                            <input wire:model.lazy="productions.{{ $i }}.plan_qty" type="text" inputmode="numeric"
                                class="w-full px-1 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 text-center">
                        </td>
                        <td class="p-px">
                            {{-- lazy → auto-fill Act H on blur --}}
                            <input wire:model.lazy="productions.{{ $i }}.act_qty" type="text" inputmode="numeric"
                                class="w-full px-1 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 text-center">
                        </td>
                        <td class="p-px">
                            {{-- Plan H: auto-filled, dimmed style to signal read-only intent --}}
                            <input wire:model="productions.{{ $i }}.plan_h" type="text" inputmode="decimal" readonly
                                class="w-full px-1 py-1.5 text-xs border-0 bg-gray-50 focus:outline-none text-center text-gray-400 cursor-default select-none">
                        </td>
                        <td class="p-px">
                            {{-- Act H: auto-filled but user can override; live for calcProcess --}}
                            <input wire:model.live="productions.{{ $i }}.act_h" type="text" inputmode="decimal"
                                class="w-full px-1 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 text-center">
                        </td>
                    </tr>
                    @endforeach
                </tbody>
            </table>
        </div>

        {{-- ── Absence ────────────────────────────────────────────────── --}}
        <div class="flex-1 min-w-0 bg-white border border-gray-300 rounded-sm">
            <div class="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-b border-gray-200">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700">Absence</span>
                <div class="flex gap-1">
                    <button wire:click="addAbsenceRow"
                        class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-green-50 text-green-700 border border-green-300 rounded-sm cursor-pointer">+ Add</button>
                    <button wire:click="removeLastAbsenceRow"
                        class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-red-50 text-red-600 border border-red-300 rounded-sm cursor-pointer">× Del</button>
                </div>
            </div>
            <table class="w-full text-xs">
                <thead>
                    <tr class="bg-gray-100 border-b border-gray-200">
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-24">NIK</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Name</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-28">Note</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-14">Hour</th>
                    </tr>
                </thead>
                <tbody>
                    @foreach($absences as $i => $row)
                    <tr wire:key="abs-{{ $i }}" class="border-b border-gray-100">
                        <td class="p-px">
                            <input wire:model="absences.{{ $i }}.nik" type="text"
                                class="w-full px-2 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50">
                        </td>
                        <td class="p-px">
                            <input wire:model="absences.{{ $i }}.name" type="text"
                                class="w-full px-2 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50">
                        </td>
                        <td class="p-px">
                            <select wire:model="absences.{{ $i }}.note"
                                class="w-full px-1 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                @foreach(['Sakit','Izin','Alpa','Cuti','Sholat Jumat','Terlambat','Lainnya'] as $nt)
                                <option>{{ $nt }}</option>
                                @endforeach
                            </select>
                        </td>
                        <td class="p-px">
                            <input wire:model.live="absences.{{ $i }}.hour" type="text" inputmode="decimal"
                                class="w-full px-1 py-1.5 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 text-center">
                        </td>
                    </tr>
                    @endforeach
                </tbody>
            </table>
        </div>

        {{-- ── Calculation Hour ──────────────────────────────────────── --}}
        <div class="bg-white border border-gray-300 rounded-sm flex-shrink-0" style="width: 210px;">
            <div class="px-3 py-1.5 bg-gray-50 border-b border-gray-200">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700">Calculation Hour</span>
            </div>
            <table class="w-full text-xs">
                <tbody>
                    @php
                        $calcRows = [
                            ['Process',     $calcProcess,     false],
                            ['Preparation', $calcPreparation, true ],
                            ['Quality',     $calcQuality,     false],
                            ['Line Stop',   $calcLineStop,    false],
                            ['Absence',     $calcAbsence,     false],
                            ['Sholat',      $calcSholat,      true ],
                            ['TOTAL',       $calcTotal,       false],
                        ];
                    @endphp
                    @foreach($calcRows as [$label, $value, $muted])
                    <tr class="border-b border-gray-100">
                        <td class="px-3 py-1 {{ $muted ? 'text-gray-400' : 'text-gray-600' }}">{{ $label }}</td>
                        <td class="px-3 py-1 text-right font-mono {{ $muted ? 'text-gray-400' : 'text-gray-700' }}">
                            {{ number_format((float)$value, 4) }}
                        </td>
                    </tr>
                    @endforeach
                    {{-- BALANCE row — green if balanced, red otherwise --}}
                    <tr class="{{ $calcBalanceOk ? 'bg-green-50' : 'bg-red-50' }}">
                        <td class="py-1.5 pl-2 pr-2 font-bold text-gray-800 border-l-4 {{ $calcBalanceOk ? 'border-green-500' : 'border-red-500' }}">
                            BALANCE
                        </td>
                        <td class="px-3 py-1.5 text-right font-mono font-bold {{ $calcBalanceOk ? 'text-green-600' : 'text-red-600' }}">
                            {{ number_format((float)$calcBalance, 4) }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

    </div>{{-- end 3-panel --}}

    {{-- ── IN HOUSE (REJECT) AND MARKET CLAIM ─────────────────────── --}}
    <div class="bg-white border border-gray-300 rounded-sm">
        <div class="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-b border-gray-200">
            <span class="text-xs font-bold uppercase tracking-wide text-gray-700">In House (Reject) and Market Claim</span>
            <div class="flex gap-1">
                <button wire:click="addInhouseRow"
                    class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-green-50 text-green-700 border border-green-300 rounded-sm cursor-pointer">+ Add</button>
                <button wire:click="removeLastInhouseRow"
                    class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-red-50 text-red-600 border border-red-300 rounded-sm cursor-pointer">× Del</button>
            </div>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-xs" style="min-width: 980px;">
                <thead>
                    <tr class="bg-gray-100 border-b border-gray-200">
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-8">No</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-20">Model</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-18">Op/ST</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Item</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-12">QTY</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-14">Satuan</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Cause / Penyebab</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Action / Perbaikan</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-22">Factor</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-14">Hour</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-14 text-red-500">Lost ★</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-16">Status</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($inhouse as $i => $row)
                    <tr wire:key="inh-{{ $i }}" class="border-b border-gray-100">
                        <td class="px-2 py-1 text-center text-gray-400">{{ $i + 1 }}</td>
                        <td class="p-px">
                            @if(!empty($shopModels))
                            <select wire:model.live="inhouse.{{ $i }}.model"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                @foreach($shopModels as $sm)
                                <option value="{{ $sm['name'] }}">{{ $sm['name'] }}</option>
                                @endforeach
                            </select>
                            @else
                            <input wire:model.live="inhouse.{{ $i }}.model" type="text"
                                class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50">
                            @endif
                        </td>
                        <td class="p-px">
                            <select wire:model="inhouse.{{ $i }}.op_st"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                <option value=""></option>
                                @foreach($opNumbers as $op)
                                <option>{{ $op }}</option>
                                @endforeach
                            </select>
                        </td>
                        <td class="p-px"><input wire:model="inhouse.{{ $i }}.item" type="text" class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"></td>
                        <td class="p-px">
                            <input wire:model.lazy="inhouse.{{ $i }}.qty" type="text" inputmode="decimal"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 text-center">
                        </td>
                        <td class="p-px">
                            <select wire:model="inhouse.{{ $i }}.satuan"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                @foreach(['Unit','Pcs','Set','Lot','Kg','Box','Sheet'] as $sat)
                                <option>{{ $sat }}</option>
                                @endforeach
                            </select>
                        </td>
                        <td class="p-px"><input wire:model="inhouse.{{ $i }}.cause" type="text" class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"></td>
                        <td class="p-px"><input wire:model="inhouse.{{ $i }}.action" type="text" class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"></td>
                        <td class="p-px">
                            <select wire:model="inhouse.{{ $i }}.factor"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                @foreach($factors as $fac)
                                <option>{{ $fac }}</option>
                                @endforeach
                            </select>
                        </td>
                        <td class="p-px">
                            {{-- Hour: auto-computed from Qty × MHU; dimmed/readonly --}}
                            <input wire:model="inhouse.{{ $i }}.hour" type="text" inputmode="decimal" readonly
                                class="w-full px-1 py-1 text-xs border-0 bg-gray-50 focus:outline-none text-center text-gray-400 cursor-default select-none">
                        </td>
                        <td class="p-px">
                            {{-- Lost: manually entered; drives calcQuality --}}
                            <input wire:model.live="inhouse.{{ $i }}.lost" type="text" inputmode="decimal"
                                class="w-full px-1 py-1 text-xs border-0 bg-red-50 focus:outline-none focus:bg-red-100 text-center font-bold text-red-700">
                        </td>
                        <td class="p-px"><input wire:model="inhouse.{{ $i }}.status" type="text" class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"></td>
                    </tr>
                    @empty
                    <tr><td colspan="12" class="px-3 py-6 text-center text-gray-400 text-xs">Belum ada data. Klik <strong>+ Add</strong> untuk menambah baris.</td></tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

    {{-- ── LINE STOP ────────────────────────────────────────────────── --}}
    <div class="bg-white border border-gray-300 rounded-sm">
        <div class="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-b border-gray-200">
            <div class="flex items-baseline gap-2">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700">Line Stop</span>
                <span class="text-xs text-gray-400">(Tool / Model Change / Man / Machine / Material / Meeting / Quality and Others)</span>
            </div>
            <div class="flex gap-1 flex-shrink-0 ml-3">
                <button wire:click="addLineStopRow"
                    class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-green-50 text-green-700 border border-green-300 rounded-sm cursor-pointer">+ Add</button>
                <button wire:click="removeLastLineStopRow"
                    class="flex items-center gap-0.5 px-2 py-0.5 text-xs bg-red-50 text-red-600 border border-red-300 rounded-sm cursor-pointer">× Del</button>
            </div>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-xs" style="min-width: 960px;">
                <thead>
                    <tr class="bg-gray-100 border-b border-gray-200">
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-8">No</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-20">Model</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-18">Op/ST</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Problem / Masalah</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Cause / Penyebab</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide">Action / Perbaikan</th>
                        <th class="px-2 py-1.5 text-left font-medium text-gray-500 uppercase tracking-wide w-22">Factor</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-16">Start</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-16">End</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-14">Stop</th>
                        <th class="px-2 py-1.5 text-center font-medium text-gray-500 uppercase tracking-wide w-14 text-red-500">Lost ★</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($lineStops as $i => $row)
                    <tr wire:key="ls-{{ $i }}" class="border-b border-gray-100">
                        <td class="px-2 py-1 text-center text-gray-400">{{ $i + 1 }}</td>
                        <td class="p-px">
                            @if(!empty($shopModels))
                            <select wire:model="lineStops.{{ $i }}.model"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                @foreach($shopModels as $sm)
                                <option value="{{ $sm['name'] }}">{{ $sm['name'] }}</option>
                                @endforeach
                            </select>
                            @else
                            <input wire:model="lineStops.{{ $i }}.model" type="text"
                                class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50">
                            @endif
                        </td>
                        <td class="p-px">
                            <select wire:model="lineStops.{{ $i }}.op_st"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                <option value=""></option>
                                @foreach($opNumbers as $op)
                                <option>{{ $op }}</option>
                                @endforeach
                            </select>
                        </td>
                        <td class="p-px"><input wire:model="lineStops.{{ $i }}.problem" type="text" class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"></td>
                        <td class="p-px"><input wire:model="lineStops.{{ $i }}.cause"   type="text" class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"></td>
                        <td class="p-px"><input wire:model="lineStops.{{ $i }}.action"  type="text" class="w-full px-2 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50"></td>
                        <td class="p-px">
                            <select wire:model="lineStops.{{ $i }}.factor"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 cursor-pointer">
                                @foreach($factors as $fac)
                                <option>{{ $fac }}</option>
                                @endforeach
                            </select>
                        </td>
                        <td class="p-px">
                            {{-- wire:model.lazy → calcLineStopStop fires on blur --}}
                            <input wire:model.lazy="lineStops.{{ $i }}.start" type="time"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 text-center">
                        </td>
                        <td class="p-px">
                            <input wire:model.lazy="lineStops.{{ $i }}.end" type="time"
                                class="w-full px-1 py-1 text-xs border-0 bg-transparent focus:outline-none focus:bg-gray-50 text-center">
                        </td>
                        <td class="p-px">
                            {{-- Stop: auto-computed from time diff; readonly --}}
                            <input wire:model="lineStops.{{ $i }}.stop" type="text" readonly
                                class="w-full px-1 py-1 text-xs border-0 bg-gray-50 focus:outline-none text-center text-gray-400 cursor-default select-none">
                        </td>
                        <td class="p-px">
                            {{-- Lost: manually entered; drives calcLineStop --}}
                            <input wire:model.live="lineStops.{{ $i }}.lost" type="text" inputmode="decimal"
                                class="w-full px-1 py-1 text-xs border-0 bg-red-50 focus:outline-none focus:bg-red-100 text-center font-bold text-red-700">
                        </td>
                    </tr>
                    @empty
                    <tr><td colspan="11" class="px-3 py-6 text-center text-gray-400 text-xs">Belum ada data. Klik <strong>+ Add</strong> untuk menambah baris.</td></tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

    {{-- ── Footer ──────────────────────────────────────────────────── --}}
    <div class="flex items-center justify-end gap-2 pb-2">
        <button wire:click="resetForm"
            class="px-5 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">
            Reset
        </button>
        <button wire:click="save"
            wire:loading.attr="disabled"
            class="px-5 py-1.5 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">
            <span wire:loading.remove wire:target="save">Simpan Laporan</span>
            <span wire:loading wire:target="save">Menyimpan...</span>
        </button>
    </div>

</div>
