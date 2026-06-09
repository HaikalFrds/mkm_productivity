<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class DailyReport extends Model
{
    protected $fillable = [
        'user_id',
        'date',
        'shift',
        'section',
        'hour',
        'ot',
        'hari_pengganti',
        'coordinator',
        'approved_by',
        'checked_by',
        'status',
    ];

    protected $casts = [
        'date'           => 'date',
        'hour'           => 'float',
        'ot'             => 'float',
        'hari_pengganti' => 'boolean',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function productions(): HasMany
    {
        return $this->hasMany(DailyProduction::class, 'report_id');
    }

    public function problems(): HasMany
    {
        return $this->hasMany(ProblemRecord::class, 'report_id');
    }

    public function manpower(): HasMany
    {
        return $this->hasMany(Manpower::class, 'report_id');
    }

    public function absen(): HasMany
    {
        return $this->hasMany(Absen::class, 'report_id');
    }

    public function inhouseClaims(): HasMany
    {
        return $this->hasMany(InhouseClaim::class, 'report_id');
    }
}
