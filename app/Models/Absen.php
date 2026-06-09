<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Absen extends Model
{
    protected $fillable = [
        'report_id',
        'no',
        'nama',
        'nik_absen',
        'shop',
        'keterangan',
        'hour',
    ];

    protected $casts = [
        'hour' => 'float',
    ];

    public function report(): BelongsTo
    {
        return $this->belongsTo(DailyReport::class, 'report_id');
    }
}
