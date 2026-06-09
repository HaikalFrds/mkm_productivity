<div class="space-y-3">

    {{-- ── Tab navigation ──────────────────────────────────────────────── --}}
    <div class="bg-white border border-gray-200 rounded">
        <div class="flex border-b border-gray-200">
            @foreach([['data_master','Data Master'],['user','User']] as [$key,$label])
            <button wire:click="switchTab('{{ $key }}')"
                class="px-6 py-2.5 text-xs font-medium border-b-2 transition-colors cursor-pointer
                       {{ $tab === $key
                           ? 'border-red-600 text-red-600'
                           : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300' }}">
                {{ $label }}
            </button>
            @endforeach
        </div>
    </div>

    {{-- ── Flash ──────────────────────────────────────────────────────── --}}
    @if($success)
    <div class="bg-green-50 border border-green-200 text-green-700 text-xs px-4 py-2 rounded flex items-center justify-between">
        <span>✓ {{ $success }}</span>
        <button wire:click="$set('success',null)" class="text-green-500 hover:text-green-700 ml-4">✕</button>
    </div>
    @endif
    @if($error)
    <div class="bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-2 rounded flex items-center justify-between">
        <span>{{ $error }}</span>
        <button wire:click="$set('error',null)" class="text-red-400 hover:text-red-600 ml-4">✕</button>
    </div>
    @endif

    {{-- ── Confirm delete ──────────────────────────────────────────────── --}}
    @if($deleteId)
    <div class="bg-red-50 border border-red-200 text-xs px-4 py-3 rounded flex items-center justify-between gap-4">
        <span class="text-red-700">Hapus <strong>"{{ $deleteName }}"</strong>? Tindakan ini tidak bisa dibatalkan.</span>
        <div class="flex gap-2 flex-shrink-0">
            <button wire:click="doDelete" class="px-3 py-1 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">Ya, Hapus</button>
            <button wire:click="cancelDelete" class="px-3 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
        </div>
    </div>
    @endif

    {{-- ══════════════════════════════════════════════════════════════════ --}}
    {{-- ── TAB: DATA MASTER ──────────────────────────────────────────── --}}
    {{-- ══════════════════════════════════════════════════════════════════ --}}
    @if($tab === 'data_master')

    {{-- Row atas: Section (kiri, sempit) + Shift (kanan, lebih lebar) --}}
    <div class="flex gap-3 items-start">

        {{-- ── Section / Shop card ──────────────────────────────────── --}}
        <div class="bg-white border border-gray-200 rounded" style="width:260px;flex-shrink:0;">
            <div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gray-50">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700 border-l-2 border-red-600 pl-2">Shop</span>
                <button wire:click="openAdd('section')"
                    class="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">
                    + Tambah
                </button>
            </div>

            @if($formOpen && $formContext === 'section')
            <div class="px-4 py-3 border-b border-gray-200 bg-blue-50">
                <label class="block text-xs text-gray-500 mb-1">Nama Shop *</label>
                <input wire:model="fSecName" type="text" placeholder="Contoh: CAM SHAFT"
                    class="border border-gray-300 rounded px-2 py-1.5 text-xs w-full mb-2 focus:outline-none focus:border-red-400">
                <div class="flex gap-2">
                    <button wire:click="save" class="px-4 py-1.5 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">{{ $formMode==='add'?'Tambah':'Simpan' }}</button>
                    <button wire:click="closeForm" class="px-4 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
                </div>
            </div>
            @endif

            <table class="w-full text-xs">
                <thead>
                    <tr class="bg-gray-100 border-b border-gray-200">
                        <th class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-10">No</th>
                        <th class="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wide">Nama</th>
                        <th class="px-3 py-2 text-right font-medium text-gray-500 uppercase tracking-wide w-20">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($sections as $i => $row)
                    <tr class="border-b border-gray-100 hover:bg-gray-50">
                        <td class="px-3 py-2 text-center text-gray-400">{{ $i+1 }}</td>
                        <td class="px-3 py-2 text-gray-800 font-medium">{{ $row['name'] }}</td>
                        <td class="px-3 py-2 text-right whitespace-nowrap">
                            <button wire:click="openEdit({{ $row['id'] }},'section')" class="text-xs text-blue-600 hover:text-blue-800 mr-1 cursor-pointer">Edit</button>
                            <button wire:click="confirmDelete({{ $row['id'] }},'{{ addslashes($row['name']) }}','section')" class="text-xs text-red-500 hover:text-red-700 cursor-pointer">Del</button>
                        </td>
                    </tr>
                    @empty
                    <tr><td colspan="3" class="px-3 py-6 text-center text-gray-400">Belum ada data.</td></tr>
                    @endforelse
                </tbody>
            </table>
        </div>

        {{-- ── Shift card ───────────────────────────────────────────── --}}
        <div class="bg-white border border-gray-200 rounded flex-1 min-w-0">
            <div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gray-50">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700 border-l-2 border-red-600 pl-2">Shift</span>
                <button wire:click="openAdd('shift')"
                    class="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">
                    + Tambah Shift
                </button>
            </div>

            @if($formOpen && $formContext === 'shift')
            <div class="px-4 py-3 border-b border-gray-200 bg-blue-50">
                <div class="flex items-end gap-3 flex-wrap">
                    <div>
                        <label class="block text-xs text-gray-500 mb-1">Nama Shift *</label>
                        <input wire:model="fShiftName" type="text" placeholder="Day Shift"
                            class="border border-gray-300 rounded px-2 py-1.5 text-xs w-32 focus:outline-none focus:border-red-400">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 mb-1">Jam Mulai</label>
                        <input wire:model="fShiftStart" type="time"
                            class="border border-gray-300 rounded px-2 py-1.5 text-xs w-24 focus:outline-none focus:border-red-400">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 mb-1">Jam Selesai</label>
                        <input wire:model="fShiftEnd" type="time"
                            class="border border-gray-300 rounded px-2 py-1.5 text-xs w-24 focus:outline-none focus:border-red-400">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 mb-1">WH (H)</label>
                        <input wire:model.live="fShiftHours" type="text" inputmode="decimal" placeholder="8"
                            class="border border-gray-300 rounded px-2 py-1.5 text-xs w-16 text-center focus:outline-none focus:border-red-400">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 mb-1">Prep (mnt)</label>
                        <input wire:model.live="fShiftPrep" type="text" inputmode="decimal" placeholder="15"
                            class="border border-gray-300 rounded px-2 py-1.5 text-xs w-16 text-center focus:outline-none focus:border-red-400">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 mb-1">Other (mnt)</label>
                        <input wire:model.live="fShiftSholat" type="text" inputmode="decimal" placeholder="10"
                            class="border border-gray-300 rounded px-2 py-1.5 text-xs w-16 text-center focus:outline-none focus:border-red-400">
                    </div>
                    <div class="flex gap-2 self-end">
                        <button wire:click="save" class="px-4 py-1.5 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">{{ $formMode==='add'?'Tambah':'Simpan' }}</button>
                        <button wire:click="closeForm" class="px-4 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
                    </div>
                </div>
                @php
                    $prepH  = round((float)($fShiftPrep ?: 0) / 60, 4);
                    $otherH = round((float)($fShiftSholat ?: 0) / 60, 4);
                @endphp
                <p class="mt-1.5 text-xs text-gray-400">
                    Prep = {{ number_format($prepH,4) }} H &nbsp;|&nbsp; Other = {{ number_format($otherH,4) }} H
                </p>
            </div>
            @endif

            <div class="overflow-x-auto">
            <table class="w-full text-xs">
                <thead>
                    <tr class="bg-gray-100 border-b border-gray-200">
                        <th class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-10">No</th>
                        <th class="px-3 py-2 text-left font-medium text-gray-500 uppercase tracking-wide">Nama Shift</th>
                        <th class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-16">Mulai</th>
                        <th class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-16">Selesai</th>
                        <th class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-16">WH (H)</th>
                        <th class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-20">Prep (mnt)</th>
                        <th class="px-3 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-20">Other (mnt)</th>
                        <th class="px-3 py-2 text-right font-medium text-gray-500 uppercase tracking-wide w-28">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($shifts as $i => $row)
                    <tr class="border-b border-gray-100 hover:bg-gray-50">
                        <td class="px-3 py-2 text-center text-gray-400">{{ $i+1 }}</td>
                        <td class="px-3 py-2 text-gray-800 font-medium">{{ $row['name'] }}</td>
                        <td class="px-3 py-2 text-center font-mono text-gray-600">{{ $row['start_time'] ? substr($row['start_time'],0,5) : '—' }}</td>
                        <td class="px-3 py-2 text-center font-mono text-gray-600">{{ $row['end_time'] ? substr($row['end_time'],0,5) : '—' }}</td>
                        <td class="px-3 py-2 text-center font-mono font-bold text-gray-800">{{ number_format((float)$row['total_hours'],1) }}</td>
                        <td class="px-3 py-2 text-center text-gray-600">{{ $row['preparation_min'] }}</td>
                        <td class="px-3 py-2 text-center text-gray-600">{{ $row['other_min'] }}</td>
                        <td class="px-3 py-2 text-right whitespace-nowrap">
                            <button wire:click="openEdit({{ $row['id'] }},'shift')" class="text-xs text-blue-600 hover:text-blue-800 mr-2 cursor-pointer">Edit</button>
                            <button wire:click="confirmDelete({{ $row['id'] }},'{{ addslashes($row['name']) }}','shift')" class="text-xs text-red-500 hover:text-red-700 cursor-pointer">Hapus</button>
                        </td>
                    </tr>
                    @empty
                    <tr><td colspan="8" class="px-3 py-6 text-center text-gray-400">Belum ada data shift.</td></tr>
                    @endforelse
                </tbody>
            </table>
            </div>
        </div>
    </div>{{-- end row atas --}}

    {{-- ── Shop Model card ──────────────────────────────────────────── --}}
    <div class="bg-white border border-gray-200 rounded">
        <div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gray-50 flex-wrap gap-2">
            <div class="flex items-center gap-3">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700 border-l-2 border-red-600 pl-2">Model per Shop</span>
                <span class="text-xs text-gray-500 font-bold">SHOP :</span>
                <select wire:model.live="smFilter"
                    class="border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:border-red-400 bg-white cursor-pointer">
                    @foreach($sections as $sec)
                    <option value="{{ $sec['id'] }}">{{ $sec['name'] }}</option>
                    @endforeach
                </select>
            </div>
            <button wire:click="openAdd('shop_model')"
                class="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">
                + Tambah Model
            </button>
        </div>

        @if($formOpen && $formContext === 'shop_model')
        <div class="px-4 py-3 border-b border-gray-200 bg-blue-50">
            <div class="flex items-end gap-3 flex-wrap">
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Nama Model *</label>
                    <input wire:model="fSmName" type="text" placeholder="Contoh: 4G15"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-28 focus:outline-none focus:border-red-400">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">MHU (mnt/unit) *</label>
                    <input wire:model.live="fSmMhu" type="text" inputmode="decimal" placeholder="4.91"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-28 text-center focus:outline-none focus:border-red-400">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Cycle Time (s/unit)</label>
                    <input wire:model="fSmCycle" type="text" inputmode="decimal" placeholder="0"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-24 text-center focus:outline-none focus:border-red-400">
                </div>
                <div class="flex gap-2 self-end">
                    <button wire:click="save" class="px-4 py-1.5 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">{{ $formMode==='add'?'Tambah':'Simpan' }}</button>
                    <button wire:click="closeForm" class="px-4 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
                </div>
            </div>
            @php
                $mnt = (float)($fSmMhu ?: 0);
                $h   = $mnt > 0 ? round($mnt / 60, 6) : 0;
            @endphp
            <p class="mt-1.5 text-xs text-gray-400">
                = {{ number_format($h,6) }} H/unit &nbsp;|&nbsp;
                Contoh: 10 unit × {{ number_format($mnt,2) }} mnt = {{ number_format(10 * $mnt, 1) }} mnt
            </p>
        </div>
        @endif

        <table class="w-full text-xs">
            <thead>
                <tr class="bg-gray-100 border-b border-gray-200">
                    <th class="px-4 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-12">No</th>
                    <th class="px-4 py-2 text-left font-medium text-gray-500 uppercase tracking-wide">Model</th>
                    <th class="px-4 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-36">H/unit (DB)</th>
                    <th class="px-4 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-32">mnt/unit</th>
                    <th class="px-4 py-2 text-right font-medium text-gray-500 uppercase tracking-wide w-28">Aksi</th>
                </tr>
            </thead>
            <tbody>
                @forelse($shopModels as $i => $row)
                <tr class="border-b border-gray-100 hover:bg-gray-50">
                    <td class="px-4 py-2 text-center text-gray-400">{{ $i+1 }}</td>
                    <td class="px-4 py-2 text-gray-800 font-medium">{{ $row['model_name'] }}</td>
                    <td class="px-4 py-2 text-center font-mono text-gray-500 text-xs">{{ number_format((float)$row['working_hour'],6) }}</td>
                    <td class="px-4 py-2 text-center font-mono font-bold text-gray-800">{{ number_format((float)$row['working_hour'] * 60, 2) }}</td>
                    <td class="px-4 py-2 text-right whitespace-nowrap">
                        <button wire:click="openEdit({{ $row['id'] }},'shop_model')" class="text-xs text-blue-600 hover:text-blue-800 mr-2 cursor-pointer">Edit</button>
                        <button wire:click="confirmDelete({{ $row['id'] }},'{{ addslashes($row['model_name']) }}','shop_model')" class="text-xs text-red-500 hover:text-red-700 cursor-pointer">Hapus</button>
                    </td>
                </tr>
                @empty
                <tr><td colspan="5" class="px-4 py-6 text-center text-gray-400">
                    {{ empty($sections) ? 'Belum ada section.' : 'Belum ada model untuk shop ini.' }}
                </td></tr>
                @endforelse
            </tbody>
        </table>
    </div>

    {{-- ── OP Number card ───────────────────────────────────────────── --}}
    <div class="bg-white border border-gray-200 rounded">
        <div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gray-50 flex-wrap gap-2">
            <div class="flex items-center gap-3">
                <span class="text-xs font-bold uppercase tracking-wide text-gray-700 border-l-2 border-red-600 pl-2">OP Number per Shop</span>
                <span class="text-xs text-gray-500 font-bold">SHOP :</span>
                <select wire:model.live="opFilter"
                    class="border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:border-red-400 bg-white cursor-pointer">
                    @foreach($sections as $sec)
                    <option value="{{ $sec['id'] }}">{{ $sec['name'] }}</option>
                    @endforeach
                </select>
            </div>
            <button wire:click="openAdd('op_number')"
                class="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">
                + Tambah OP
            </button>
        </div>

        @if($formOpen && $formContext === 'op_number')
        <div class="px-4 py-3 border-b border-gray-200 bg-blue-50">
            <div class="flex items-end gap-3 flex-wrap">
                <div>
                    <label class="block text-xs text-gray-500 mb-1">OP Number *</label>
                    <input wire:model="fOpNo" type="text" placeholder="Contoh: CS-10"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-28 focus:outline-none focus:border-red-400">
                </div>
                <div class="flex gap-2">
                    <button wire:click="save" class="px-4 py-1.5 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">Tambah</button>
                    <button wire:click="closeForm" class="px-4 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
                </div>
            </div>
        </div>
        @endif

        <table class="w-full text-xs">
            <thead>
                <tr class="bg-gray-100 border-b border-gray-200">
                    <th class="px-4 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-12">No</th>
                    <th class="px-4 py-2 text-left font-medium text-gray-500 uppercase tracking-wide">OP Number</th>
                    <th class="px-4 py-2 text-right font-medium text-gray-500 uppercase tracking-wide w-24">Aksi</th>
                </tr>
            </thead>
            <tbody>
                @forelse($opNumbers as $i => $row)
                <tr class="border-b border-gray-100 hover:bg-gray-50">
                    <td class="px-4 py-2 text-center text-gray-400">{{ $i+1 }}</td>
                    <td class="px-4 py-2 text-gray-800 font-medium font-mono">{{ $row['op_no'] }}</td>
                    <td class="px-4 py-2 text-right">
                        <button wire:click="confirmDelete({{ $row['id'] }},'{{ addslashes($row['op_no']) }}','op_number')" class="text-xs text-red-500 hover:text-red-700 cursor-pointer">Hapus</button>
                    </td>
                </tr>
                @empty
                <tr><td colspan="3" class="px-4 py-6 text-center text-gray-400">
                    {{ empty($sections) ? 'Belum ada section.' : 'Belum ada OP Number untuk shop ini.' }}
                </td></tr>
                @endforelse
            </tbody>
        </table>
    </div>

    {{-- ── Kategori Masalah card ─────────────────────────────────────── --}}
    <div class="bg-white border border-gray-200 rounded">
        <div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gray-50">
            <span class="text-xs font-bold uppercase tracking-wide text-gray-700 border-l-2 border-red-600 pl-2">Kategori Masalah</span>
            <button wire:click="openAdd('category')"
                class="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">
                + Tambah Kategori
            </button>
        </div>

        @if($formOpen && $formContext === 'category')
        <div class="px-4 py-3 border-b border-gray-200 bg-blue-50">
            <div class="flex items-end gap-3 flex-wrap">
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Group *</label>
                    <select wire:model="fCatGroup"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-40 focus:outline-none focus:border-red-400 bg-white cursor-pointer">
                        <option value="0">— pilih —</option>
                        @foreach($groups as $g)
                        <option value="{{ $g['id'] }}">{{ $g['name'] }}</option>
                        @endforeach
                    </select>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Nama Kategori *</label>
                    <input wire:model="fCatName" type="text" placeholder="Nama kategori"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-48 focus:outline-none focus:border-red-400">
                </div>
                <div class="flex gap-2">
                    <button wire:click="save" class="px-4 py-1.5 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">{{ $formMode==='add'?'Tambah':'Simpan' }}</button>
                    <button wire:click="closeForm" class="px-4 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
                </div>
            </div>
        </div>
        @endif

        {{-- Flat table: No, Group, Nama, Aksi --}}
        <table class="w-full text-xs">
            <thead>
                <tr class="bg-gray-100 border-b border-gray-200">
                    <th class="px-4 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-12">No</th>
                    <th class="px-4 py-2 text-left font-medium text-gray-500 uppercase tracking-wide w-36">Group</th>
                    <th class="px-4 py-2 text-left font-medium text-gray-500 uppercase tracking-wide">Nama Kategori</th>
                    <th class="px-4 py-2 text-right font-medium text-gray-500 uppercase tracking-wide w-28">Aksi</th>
                </tr>
            </thead>
            <tbody>
                @forelse($categories as $i => $cat)
                <tr class="border-b border-gray-100 hover:bg-gray-50">
                    <td class="px-4 py-2 text-center text-gray-400">{{ $i+1 }}</td>
                    <td class="px-4 py-2 text-gray-500">{{ $cat['group_name'] }}</td>
                    <td class="px-4 py-2 text-gray-800 font-medium">{{ $cat['name'] }}</td>
                    <td class="px-4 py-2 text-right whitespace-nowrap">
                        <button wire:click="openEdit({{ $cat['id'] }},'category')" class="text-xs text-blue-600 hover:text-blue-800 mr-2 cursor-pointer">Edit</button>
                        <button wire:click="confirmDelete({{ $cat['id'] }},'{{ addslashes($cat['name']) }}','category')" class="text-xs text-red-500 hover:text-red-700 cursor-pointer">Hapus</button>
                    </td>
                </tr>
                @empty
                <tr><td colspan="4" class="px-4 py-6 text-center text-gray-400">Belum ada kategori masalah.</td></tr>
                @endforelse
            </tbody>
        </table>
    </div>

    @endif {{-- end data_master --}}

    {{-- ══════════════════════════════════════════════════════════════════ --}}
    {{-- ── TAB: USER ──────────────────────────────────────────────────── --}}
    {{-- ══════════════════════════════════════════════════════════════════ --}}
    @if($tab === 'user')

    <div class="bg-white border border-gray-200 rounded">
        <div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gray-50">
            <span class="text-xs font-bold uppercase tracking-wide text-gray-700 border-l-2 border-red-600 pl-2">Daftar User</span>
            <button wire:click="openAddUser"
                class="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">
                + Tambah User
            </button>
        </div>

        {{-- Form Tambah User --}}
        @if($userFormOpen && $userFormMode === 'add')
        <div class="px-4 py-3 border-b border-gray-200 bg-blue-50">
            <div class="flex items-end gap-3 flex-wrap">
                <div>
                    <label class="block text-xs text-gray-500 mb-1">NIK *</label>
                    <input wire:model="fUserNik" type="text" placeholder="NIK"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-28 focus:outline-none focus:border-red-400">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Nama *</label>
                    <input wire:model="fUserName" type="text" placeholder="Nama Lengkap"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-44 focus:outline-none focus:border-red-400">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Role</label>
                    <select wire:model="fUserRole"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-28 focus:outline-none focus:border-red-400 bg-white cursor-pointer">
                        <option value="operator">operator</option>
                        <option value="admin">admin</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Password *</label>
                    <input wire:model="fUserPass" type="password" placeholder="Password"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-36 focus:outline-none focus:border-red-400">
                </div>
                <div class="flex gap-2">
                    <button wire:click="saveUser" class="px-4 py-1.5 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">Tambah</button>
                    <button wire:click="closeUserForm" class="px-4 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
                </div>
            </div>
        </div>
        @endif

        {{-- Form Reset Password --}}
        @if($userFormOpen && $userFormMode === 'reset_pw')
        <div class="px-4 py-3 border-b border-gray-200 bg-yellow-50">
            <div class="flex items-end gap-3 flex-wrap">
                <div>
                    <label class="block text-xs text-gray-500 mb-1">Password Baru *</label>
                    <input wire:model="fUserNewPass" type="password" placeholder="Password baru"
                        class="border border-gray-300 rounded px-2 py-1.5 text-xs w-44 focus:outline-none focus:border-red-400">
                </div>
                <div class="flex gap-2">
                    <button wire:click="saveUser" class="px-4 py-1.5 text-xs font-bold text-white bg-red-600 rounded hover:bg-red-700 cursor-pointer">Reset Password</button>
                    <button wire:click="closeUserForm" class="px-4 py-1.5 text-xs text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">Batal</button>
                </div>
            </div>
        </div>
        @endif

        <table class="w-full text-xs">
            <thead>
                <tr class="bg-gray-100 border-b border-gray-200">
                    <th class="px-4 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-12">No</th>
                    <th class="px-4 py-2 text-left font-medium text-gray-500 uppercase tracking-wide w-28">NIK</th>
                    <th class="px-4 py-2 text-left font-medium text-gray-500 uppercase tracking-wide">Nama</th>
                    <th class="px-4 py-2 text-center font-medium text-gray-500 uppercase tracking-wide w-24">Role</th>
                    <th class="px-4 py-2 text-right font-medium text-gray-500 uppercase tracking-wide w-44">Aksi</th>
                </tr>
            </thead>
            <tbody>
                @forelse($users as $i => $u)
                <tr class="border-b border-gray-100 hover:bg-gray-50">
                    <td class="px-4 py-2 text-center text-gray-400">{{ $i+1 }}</td>
                    <td class="px-4 py-2 font-mono text-gray-700">{{ $u['nik'] ?? '—' }}</td>
                    <td class="px-4 py-2 text-gray-800 font-medium">{{ $u['name'] }}</td>
                    <td class="px-4 py-2 text-center">
                        <span class="px-2 py-0.5 text-xs rounded
                            {{ $u['role'] === 'admin' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600' }}">
                            {{ $u['role'] }}
                        </span>
                    </td>
                    <td class="px-4 py-2 text-right whitespace-nowrap">
                        <button wire:click="openResetPw({{ $u['id'] }})"
                            class="text-xs text-blue-600 hover:text-blue-800 border border-blue-200 px-2 py-0.5 rounded mr-2 cursor-pointer">
                            Reset PW
                        </button>
                        @if(!auth()->check() || auth()->id() !== $u['id'])
                        <button wire:click="confirmDelete({{ $u['id'] }},'{{ addslashes($u['name']) }}','user')"
                            class="text-xs text-red-500 hover:text-red-700 cursor-pointer">Hapus</button>
                        @else
                        <span class="text-xs text-gray-300" title="Tidak bisa hapus akun sendiri">Hapus</span>
                        @endif
                    </td>
                </tr>
                @empty
                <tr><td colspan="5" class="px-4 py-8 text-center text-gray-400">Belum ada data user.</td></tr>
                @endforelse
            </tbody>
        </table>
    </div>

    @endif {{-- end user --}}

</div>
