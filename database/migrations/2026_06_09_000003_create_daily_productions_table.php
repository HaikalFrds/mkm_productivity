<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('daily_productions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('report_id')->constrained('daily_reports')->cascadeOnDelete();
            $table->string('model')->nullable();
            $table->float('plan_unit')->default(0);
            $table->float('actual_unit')->default(0);
            $table->float('plan_whour')->default(0);
            $table->float('actual_whour')->default(0);
            $table->boolean('ot_2h')->default(false);
            $table->boolean('ot_3h')->default(false);
            $table->boolean('ot_11h')->default(false);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('daily_productions');
    }
};
