<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        // Admin default
        User::firstOrCreate(
            ['nik' => 'admin'],
            [
                'name'     => 'Administrator',
                'password' => Hash::make('admin123'),
                'role'     => 'admin',
            ]
        );

        // Operator contoh
        User::firstOrCreate(
            ['nik' => '12345'],
            [
                'name'     => 'Operator 1',
                'password' => Hash::make('12345'),
                'role'     => 'operator',
            ]
        );
    }
}
