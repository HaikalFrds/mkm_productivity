<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('inhouse_claims', function (Blueprint $table) {
            $table->id();
            $table->foreignId('report_id')->constrained('daily_reports')->cascadeOnDelete();
            $table->date('tanggal')->nullable();
            $table->string('model')->nullable();
            $table->string('op_no_st')->nullable();
            $table->string('item')->nullable();
            $table->float('qty')->default(0);
            $table->string('satuan')->nullable();
            $table->text('penyebab')->nullable();
            $table->text('tindakan')->nullable();
            $table->string('faktor')->nullable();
            $table->float('stop_hr')->default(0);
            $table->float('lost_hr')->default(0);
            $table->string('status_klaim')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('inhouse_claims');
    }
};
